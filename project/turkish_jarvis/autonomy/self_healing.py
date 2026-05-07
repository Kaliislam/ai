"""Kendi kendine düzeltme — hata yakalama, analiz, kod düzeltme, test, rollback."""

from __future__ import annotations

import asyncio
import ast
import hashlib
import importlib
import importlib.util
import inspect
import json
import logging
import subprocess
import sys
import tempfile
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger("jarvis.self_healing")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class HealingResult:
    """Bir iyileştirme (healing) işleminin sonucu."""

    success: bool = False
    original_error: str = ""
    fix_applied: bool = False
    rolled_back: bool = False
    new_code: str | None = None
    test_passed: bool = False
    healing_time: float = 0.0
    confidence: float = 0.0  # LLM'in düzeltme güveni


@dataclass
class HealingEvent:
    """İyileştirme geçmişindeki tek bir olay."""

    timestamp: datetime = field(default_factory=datetime.now)
    module: str = ""
    function: str = ""
    error_type: str = ""
    error_message: str = ""
    fix_success: bool = False
    rolled_back: bool = False
    original_code_hash: str = ""
    new_code_hash: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0


# ---------------------------------------------------------------------------
# Self-healing engine
# ---------------------------------------------------------------------------


class SelfHealingEngine:
    """Hata durumlarında otomatik düzeltme yapan motor."""

    # Sadece bu dizin altındaki dosyaları düzenlemeye izin ver
    _ALLOWED_PREFIX: str = "turkish_jarvis"

    def __init__(self, llm_client, project_dir: str = ".") -> None:
        self.llm = llm_client
        self.project_dir = Path(project_dir).resolve()
        self.backup_dir = self.project_dir / "data" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.healing_log: list[HealingEvent] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def heal_tool_error(
        self,
        tool_func: Callable,
        args: dict[str, Any],
        error: Exception,
        stack_trace: str,
    ) -> HealingResult:
        """Bir araç fonksiyonunun hatasını düzelt.

        Akış:
        1. Kaynak kodu al
        2. LLM'e analiz etmesini ve düzeltmesini iste
        3. Düzeltilmiş kodu parse et (syntax check)
        4. Orijinali yedekle
        5. Yeni kodu yaz
        6. Test et (orijinal test case'leri çalıştır)
        7. Başarılıysa kaydet, başarısızsa rollback
        """
        start = time.perf_counter()
        result = HealingResult(original_error=f"{type(error).__name__}: {error}")

        # 1. Kaynak kodu ve dosya yolunu belirle
        try:
            source = inspect.getsource(tool_func)
            file_path = Path(inspect.getfile(tool_func)).resolve()
        except (OSError, TypeError) as exc:
            logger.error("[SelfHealing] Kaynak kod alınamadı: %s", exc)
            result.healing_time = time.perf_counter() - start
            return result

        # Güvenlik: sadece izin verilen dizin altındaki dosyalar
        if not self._is_allowed_path(file_path):
            logger.warning("[SelfHealing] Dosya izin dışı: %s", file_path)
            result.healing_time = time.perf_counter() - start
            return result

        # 2. LLM düzeltmesi iste
        fixed_code, confidence, usage = await self._ask_llm_for_fix(
            source=source,
            func_name=getattr(tool_func, "__name__", "unknown"),
            args=args,
            error=error,
            stack_trace=stack_trace,
        )

        if fixed_code is None or fixed_code.strip() == source.strip():
            logger.info("[SelfHealing] LLM düzeltme üretmedi veya değişiklik yok.")
            result.healing_time = time.perf_counter() - start
            result.confidence = confidence
            return result

        # 3. Syntax kontrolü (ast.parse)
        if not self._syntax_ok(fixed_code):
            logger.error("[SelfHealing] LLM çıktısı syntax hatası içeriyor.")
            result.healing_time = time.perf_counter() - start
            result.confidence = confidence
            return result

        # 4. Orijinali yedekle
        backup = self._backup_file(file_path)

        # 5. Yeni kodu uygula
        applied = self._apply_fix(file_path, fixed_code)
        if not applied:
            logger.error("[SelfHealing] Kod uygulanamadı (syntax hatası?).")
            self._rollback(file_path, backup)
            result.healing_time = time.perf_counter() - start
            result.confidence = confidence
            return result

        result.fix_applied = True
        result.new_code = fixed_code

        # 6. Test et (orijinal test case'leri çalıştır)
        test_case = self._generate_test_from_error(error, args)
        test_passed = await self._run_test(tool_func, test_case, file_path, fixed_code)
        result.test_passed = test_passed

        if test_passed:
            logger.info("[SelfHealing] Düzeltme başarılı, test geçti.")
            result.success = True
        else:
            logger.warning("[SelfHealing] Test başarısız — rollback yapılıyor.")
            self._rollback(file_path, backup)
            result.rolled_back = True
            result.fix_applied = False
            result.new_code = None

        result.healing_time = time.perf_counter() - start
        result.confidence = confidence

        # 7. Olayı kaydet ve meta-learning'e rapor gönder
        event = HealingEvent(
            module=str(file_path.relative_to(self.project_dir)),
            function=getattr(tool_func, "__name__", "unknown"),
            error_type=type(error).__name__,
            error_message=str(error),
            fix_success=result.success,
            rolled_back=result.rolled_back,
            original_code_hash=self._hash(source),
            new_code_hash=self._hash(fixed_code) if result.fix_applied else "",
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
        )
        self.healing_log.append(event)
        await self._report_to_meta_learning(event)

        return result

    async def heal_module_error(
        self,
        module_path: str,
        error: Exception,
        stack_trace: str,
    ) -> HealingResult:
        """Bir modül dosyasının hatasını düzelt.

        Akış:
        1. Dosyayı oku
        2. Hatanın kaynağını stack trace'den bul
        3. LLM'e dosya + hata ver, düzeltmesini iste
        4. Syntax kontrolü
        5. Yedekle, uygula, test et, rollback (gerekirse)
        """
        start = time.perf_counter()
        result = HealingResult(original_error=f"{type(error).__name__}: {error}")

        file_path = self.project_dir / module_path
        file_path = file_path.resolve()

        if not self._is_allowed_path(file_path):
            logger.warning("[SelfHealing] Modül dosyası izin dışı: %s", file_path)
            result.healing_time = time.perf_counter() - start
            return result

        if not file_path.exists():
            logger.error("[SelfHealing] Dosya bulunamadı: %s", file_path)
            result.healing_time = time.perf_counter() - start
            return result

        original_code = file_path.read_text(encoding="utf-8")

        # Stack trace'den satır numarasını ve fonksiyon adını çıkar
        lineno, func_name = self._extract_location_from_trace(stack_trace)

        # LLM düzeltmesi
        fixed_code, confidence, usage = await self._ask_llm_for_module_fix(
            original_code=original_code,
            module_path=module_path,
            lineno=lineno,
            func_name=func_name,
            error=error,
            stack_trace=stack_trace,
        )

        if fixed_code is None or fixed_code.strip() == original_code.strip():
            result.healing_time = time.perf_counter() - start
            result.confidence = confidence
            return result

        if not self._syntax_ok(fixed_code):
            logger.error("[SelfHealing] Modül düzeltmesi syntax hatası içeriyor.")
            result.healing_time = time.perf_counter() - start
            result.confidence = confidence
            return result

        backup = self._backup_file(file_path)
        applied = self._apply_fix(file_path, fixed_code)
        if not applied:
            self._rollback(file_path, backup)
            result.healing_time = time.perf_counter() - start
            result.confidence = confidence
            return result

        result.fix_applied = True
        result.new_code = fixed_code

        # Modülü yeniden yükleyip test et
        test_passed = await self._reload_and_test_module(file_path, fixed_code)
        result.test_passed = test_passed

        if test_passed:
            logger.info("[SelfHealing] Modül düzeltmesi başarılı.")
            result.success = True
        else:
            logger.warning("[SelfHealing] Modül testi başarısız — rollback.")
            self._rollback(file_path, backup)
            result.rolled_back = True
            result.fix_applied = False
            result.new_code = None

        result.healing_time = time.perf_counter() - start
        result.confidence = confidence

        event = HealingEvent(
            module=module_path,
            function=func_name or "<module>",
            error_type=type(error).__name__,
            error_message=str(error),
            fix_success=result.success,
            rolled_back=result.rolled_back,
            original_code_hash=self._hash(original_code),
            new_code_hash=self._hash(fixed_code) if result.fix_applied else "",
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
        )
        self.healing_log.append(event)
        await self._report_to_meta_learning(event)

        return result

    def get_healing_history(self) -> list[HealingEvent]:
        """Tüm iyileştirme geçmişini döndür."""
        return list(self.healing_log)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_allowed_path(self, file_path: Path) -> bool:
        """Dosyanın proje dizini altında ve izin verilen prefix altında olduğunu kontrol et."""
        try:
            rel = file_path.relative_to(self.project_dir)
        except ValueError:
            return False
        parts = rel.parts
        return len(parts) > 0 and parts[0] == self._ALLOWED_PREFIX

    def _backup_file(self, file_path: Path) -> Path:
        """Dosyayı yedekle."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup = self.backup_dir / backup_name
        backup.write_text(file_path.read_text(encoding="utf-8"), encoding="utf-8")
        logger.info("[SelfHealing] Yedek oluşturuldu: %s", backup)
        return backup

    def _rollback(self, file_path: Path, backup: Path) -> None:
        """Yedeği geri yükle."""
        if backup.exists():
            file_path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
            logger.info("[SelfHealing] Rollback yapıldı: %s -> %s", backup, file_path)
        else:
            logger.error("[SelfHealing] Yedek bulunamadı, rollback mümkün değil!")

    def _apply_fix(self, file_path: Path, new_code: str) -> bool:
        """Yeni kodu uygula, syntax kontrolü yap."""
        if not self._syntax_ok(new_code):
            return False
        file_path.write_text(new_code, encoding="utf-8")
        return True

    def _syntax_ok(self, code: str) -> bool:
        """Python kodunun syntax doğruluğunu ast.parse ile kontrol et."""
        try:
            ast.parse(code)
            return True
        except SyntaxError as exc:
            logger.error("[SelfHealing] Syntax hatası: %s", exc)
            return False

    def _hash(self, text: str) -> str:
        """Metnin SHA-256 hash'ini döndür."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    def _generate_test_from_error(self, error: Exception, args: dict[str, Any]) -> dict[str, Any]:
        """Hatadan otomatik test case üret.

        Basitçe: aynı girdilerle tekrar çalıştır, hata farklı (veya yok) olmalı.
        """
        return {"input": args, "expected_not": str(error)}

    def _extract_location_from_trace(self, stack_trace: str) -> tuple[int | None, str]:
        """Stack trace'den satır numarası ve fonksiyon adını çıkar.

        Örnek satır:
          File ".../foo.py", line 42, in bar_func
        """
        lineno: int | None = None
        func_name: str = ""
        for line in stack_trace.strip().splitlines():
            if line.strip().startswith('File "'):
                parts = line.split(",")
                for part in parts:
                    part = part.strip()
                    if part.startswith("line "):
                        try:
                            lineno = int(part.replace("line ", ""))
                        except ValueError:
                            pass
                    elif "in " in part and "File" not in part:
                        func_name = part.split("in ")[-1].strip()
        return lineno, func_name

    # ------------------------------------------------------------------
    # LLM interaction
    # ------------------------------------------------------------------

    async def _ask_llm_for_fix(
        self,
        source: str,
        func_name: str,
        args: dict[str, Any],
        error: Exception,
        stack_trace: str,
    ) -> tuple[str | None, float, dict[str, int]]:
        """LLM'den fonksiyon düzeltmesi iste.

        Döndürür: (fixed_code, confidence, usage_dict)
        """
        prompt = self._build_tool_fix_prompt(source, func_name, args, error, stack_trace)

        try:
            response = await self.llm.chat(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Sen bir Python kod düzeltme uzmanısın. "
                            "Sadece düzeltilmiş kodu ve güven skorunu JSON olarak döndür."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                json_mode=True,
            )
        except Exception as exc:
            logger.error("[SelfHealing] LLM isteği başarısız: %s", exc)
            return None, 0.0, {}

        content = response.get("content", "") if isinstance(response, dict) else str(response)
        return self._parse_llm_fix_response(content)

    async def _ask_llm_for_module_fix(
        self,
        original_code: str,
        module_path: str,
        lineno: int | None,
        func_name: str,
        error: Exception,
        stack_trace: str,
    ) -> tuple[str | None, float, dict[str, int]]:
        """LLM'den modül düzeltmesi iste."""
        prompt = self._build_module_fix_prompt(
            original_code, module_path, lineno, func_name, error, stack_trace
        )

        try:
            response = await self.llm.chat(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Sen bir Python kod düzeltme uzmanısın. "
                            "Sadece düzeltilmiş kodu ve güven skorunu JSON olarak döndür."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                json_mode=True,
            )
        except Exception as exc:
            logger.error("[SelfHealing] LLM modül isteği başarısız: %s", exc)
            return None, 0.0, {}

        content = response.get("content", "") if isinstance(response, dict) else str(response)
        return self._parse_llm_fix_response(content)

    def _build_tool_fix_prompt(
        self,
        source: str,
        func_name: str,
        args: dict[str, Any],
        error: Exception,
        stack_trace: str,
    ) -> str:
        """Araç fonksiyonu düzeltme promptu oluştur."""
        return (
            f"Aşağıdaki Python fonksiyonu şu girdilerle çalıştırıldığında hata veriyor.\n\n"
            f"--- Fonksiyon Adı ---\n{func_name}\n\n"
            f"--- Kaynak Kod ---\n```python\n{source}\n```\n\n"
            f"--- Girdiler (args) ---\n{json.dumps(args, ensure_ascii=False, indent=2)}\n\n"
            f"--- Hata ---\n{type(error).__name__}: {error}\n\n"
            f"--- Stack Trace ---\n{stack_trace}\n\n"
            f"Lütfen:\n"
            f"1. Hatayı analiz et (kısaca).\n"
            f"2. Düzeltilmiş fonksiyonu tam olarak üret.\n"
            f"3. Güven skorunu 0.0-1.0 arasında ver.\n\n"
            f"Cevabı şu JSON formatında döndür:\n"
            f'{{\n  "analysis": "kısa analiz",\n  "fixed_code": "tam düzeltilmiş kod",\n  "confidence": 0.85\n}}'
        )

    def _build_module_fix_prompt(
        self,
        original_code: str,
        module_path: str,
        lineno: int | None,
        func_name: str,
        error: Exception,
        stack_trace: str,
    ) -> str:
        """Modül düzeltme promptu oluştur."""
        location_hint = f" (yaklaşık satır {lineno})" if lineno else ""
        return (
            f"Aşağıdaki Python modülü yüklenirken veya çalışırken hata veriyor.\n\n"
            f"--- Dosya ---\n{module_path}{location_hint}\n\n"
            f"--- Kaynak Kod ---\n```python\n{original_code}\n```\n\n"
            f"--- Hatanın Kaynağı ---\n"
            f"Fonksiyon/Alan: {func_name or 'bilinmiyor'}\n"
            f"Hata Türü: {type(error).__name__}\n"
            f"Hata Mesajı: {error}\n\n"
            f"--- Stack Trace ---\n{stack_trace}\n\n"
            f"Lütfen:\n"
            f"1. Hatayı analiz et (kısaca).\n"
            f"2. Düzeltilmiş dosya içeriğini tam olarak üret.\n"
            f"3. Güven skorunu 0.0-1.0 arasında ver.\n\n"
            f"Cevabı şu JSON formatında döndür:\n"
            f'{{\n  "analysis": "kısa analiz",\n  "fixed_code": "tam düzeltilmiş kod",\n  "confidence": 0.85\n}}'
        )

    def _parse_llm_fix_response(self, content: str) -> tuple[str | None, float, dict[str, int]]:
        """LLM yanıtından düzeltilmiş kodu, güven skorunu ve token kullanımını çıkar.

        Yanıt JSON formatında olmalı:
        {"analysis": "...", "fixed_code": "...", "confidence": 0.85}
        """
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # JSON değilse, kod bloğu aramaya çalış
            fixed_code = self._extract_code_block(content)
            return fixed_code, 0.5, {}

        fixed_code = data.get("fixed_code", "")
        confidence = float(data.get("confidence", 0.5))
        usage = data.get("usage", {})

        # Kod bloğu içindeyse temizle
        if fixed_code.startswith("```"):
            fixed_code = self._extract_code_block(fixed_code) or fixed_code

        return fixed_code, confidence, usage

    @staticmethod
    def _extract_code_block(text: str) -> str | None:
        """Markdown kod bloğundan içeriği çıkar."""
        lines = text.splitlines()
        in_block = False
        code_lines: list[str] = []
        for line in lines:
            if line.strip().startswith("```python"):
                in_block = True
                continue
            if in_block and line.strip().startswith("```"):
                in_block = False
                break
            if in_block:
                code_lines.append(line)
        return "\n".join(code_lines) if code_lines else None

    # ------------------------------------------------------------------
    # Testing
    # ------------------------------------------------------------------

    async def _run_test(
        self,
        tool_func: Callable,
        test_case: dict[str, Any],
        file_path: Path,
        new_code: str,
    ) -> bool:
        """Düzeltilmiş kodu sandbox'ta test et.

        Strateji:
        - Fonksiyonu geçici bir modülde çalıştır
        - Aynı girdilerle çağır
        - Eski hatayı tekrar etmemeli
        """
        test_input = test_case.get("input", {})
        expected_not = test_case.get("expected_not", "")

        # Geçici modül oluştur
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(new_code)
            tmp_path = Path(tmp.name)

        try:
            # Modülü yükle ve fonksiyonu çağır
            spec = importlib.util.spec_from_file_location("_healing_test", tmp_path)
            if spec is None or spec.loader is None:
                return False
            mod = importlib.util.module_from_spec(spec)
            sys.modules["_healing_test"] = mod
            spec.loader.exec_module(mod)

            # İlk fonksiyonu bul
            candidates = [
                obj
                for obj in mod.__dict__.values()
                if callable(obj) and hasattr(obj, "__name__")
            ]
            if not candidates:
                return False

            candidate = candidates[0]

            if asyncio.iscoroutinefunction(candidate):
                result = await candidate(**test_input)
            else:
                result = candidate(**test_input)

            # Eğer exception fırlatmadıysa ve eski hatayı tekrar etmediyse başarılı
            logger.debug("[SelfHealing] Test sonucu: %s", result)
            return True

        except Exception as exc:
            error_msg = str(exc)
            if expected_not and expected_not in error_msg:
                # Eski hata hâlâ var
                logger.debug("[SelfHealing] Eski hata tekrar etti: %s", exc)
                return False
            # Yeni bir hata var — bu da başarısız sayılır
            logger.debug("[SelfHealing] Yeni hata: %s", exc)
            return False
        finally:
            tmp_path.unlink(missing_ok=True)
            sys.modules.pop("_healing_test", None)

    async def _reload_and_test_module(self, file_path: Path, new_code: str) -> bool:
        """Düzeltilmiş modülü py_compile ile syntax kontrolü yap ve geçici olarak import et."""
        # 1. py_compile ile syntax kontrolü
        try:
            import py_compile
            py_compile.compile(str(file_path), doraise=True)
        except py_compile.PyCompileError as exc:
            logger.error("[SelfHealing] py_compile başarısız: %s", exc)
            return False

        # 2. Geçici import testi
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(new_code)
            tmp_path = Path(tmp.name)

        try:
            spec = importlib.util.spec_from_file_location("_healing_module_test", tmp_path)
            if spec is None or spec.loader is None:
                return False
            mod = importlib.util.module_from_spec(spec)
            sys.modules["_healing_module_test"] = mod
            spec.loader.exec_module(mod)
            return True
        except Exception as exc:
            logger.debug("[SelfHealing] Modül import testi başarısız: %s", exc)
            return False
        finally:
            tmp_path.unlink(missing_ok=True)
            sys.modules.pop("_healing_module_test", None)

    # ------------------------------------------------------------------
    # Meta-learning reporting
    # ------------------------------------------------------------------

    async def _report_to_meta_learning(self, event: HealingEvent) -> None:
        """Meta-learning modülüne iyileştirme raporu gönder.

        Şu anda sadece bir JSON dosyasına yazar. Gelecekte meta_learning.py'ye
        entegrasyon burada yapılacak.
        """
        report_path = self.project_dir / "data" / "meta_learning_reports.jsonl"
        report_path.parent.mkdir(parents=True, exist_ok=True)

        report = {
            "timestamp": event.timestamp.isoformat(),
            "module": event.module,
            "function": event.function,
            "error_type": event.error_type,
            "error_message": event.error_message,
            "fix_success": event.fix_success,
            "rolled_back": event.rolled_back,
            "original_code_hash": event.original_code_hash,
            "new_code_hash": event.new_code_hash,
        }

        with open(report_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(report, ensure_ascii=False) + "\n")

        logger.info("[SelfHealing] Meta-learning raporu yazıldı: %s", report_path)
