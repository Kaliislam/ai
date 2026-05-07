"""Otomatik yetenek edinme — internetten öğren, kod üret, test et, kaydet."""

import asyncio
import ast
import hashlib
import importlib.util
import inspect
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import httpx

logger = logging.getLogger("jarvis.auto_skill")


# ──────────────────────────────
#  Veri yapıları
# ──────────────────────────────

@dataclass
class NeedAnalysis:
    missing_skill: str
    required_inputs: list[str]
    expected_output: str
    confidence: float = 0.0


@dataclass
class ResearchResult:
    snippets: list[str] = field(default_factory=list)
    code_examples: list[str] = field(default_factory=list)
    docs: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)


@dataclass
class GeneratedSkill:
    name: str
    code: str
    schema: dict
    tests: list[dict]
    research_sources: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)
    confidence: float = 0.0


@dataclass
class TestResult:
    passed: bool
    output: str
    error: str | None
    execution_time: float


@dataclass
class SkillAcquisitionResult:
    success: bool
    skill_name: str | None
    message: str
    test_result: TestResult | None = None


# ──────────────────────────────
#  Güvenlik – AST & Sandbox
# ──────────────────────────────

FORBIDDEN_IMPORTS = frozenset(
    {
        "os.system",
        "os.popen",
        "os.spawn",
        "subprocess",
        "socket",
        "urllib",
        "urllib.request",
        "urllib2",
        "http.client",
        "ftplib",
        "telnetlib",
        "smtplib",
        "eval",
        "exec",
        "compile",
        "__import__",
        "input",
        "open",
    }
)

FORBIDDEN_NAMES = frozenset(
    {
        "eval",
        "exec",
        "compile",
        "__import__",
        "breakpoint",
    }
)


class SecurityError(Exception):
    """Üretilen kod güvenlik politikasına uymuyor."""

    pass


class SecurityChecker(ast.NodeVisitor):
    """AST üzerinden yasaklı yapıları tespit eder."""

    def __init__(self) -> None:
        self.violations: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for alias in node.names:
            mod = alias.name.split(".")[0]
            if mod in FORBIDDEN_IMPORTS or any(
                mod.startswith(fbi.split(".")[0]) for fbi in FORBIDDEN_IMPORTS if "." in fbi
            ):
                self.violations.append(f"Yasaklı import: {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        if node.module:
            mod = node.module.split(".")[0]
            if mod in FORBIDDEN_IMPORTS or any(
                mod.startswith(fbi.split(".")[0]) for fbi in FORBIDDEN_IMPORTS if "." in fbi
            ):
                self.violations.append(f"Yasaklı from-import: {node.module}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_NAMES:
            self.violations.append(f"Yasaklı fonksiyon çağrısı: {node.func.id}")
        self.generic_visit(node)


# ──────────────────────────────
#  Sandbox Runner
# ──────────────────────────────

SANDBOX_PREAMBLE = textwrap.dedent(
    r"""
    import sys, builtins
    # Yasaklı modülleri __import__ seviyesinde engelle
    _orig_import = builtins.__import__
    _forbidden_modules = {'urllib', 'urllib.request', 'ftplib', 'http.client', 'telnetlib', 'smtplib'}
    def _safe_import(name, *args, **kwargs):
        base = name.split('.')[0]
        if base in _forbidden_modules or name in _forbidden_modules:
            raise ImportError(f"Import '{name}' sandbox tarafından engellendi.")
        return _orig_import(name, *args, **kwargs)
    builtins.__import__ = _safe_import
    # open() fonksiyonunu geçici olarak devre dışı bırak (dosya erişimini engelle)
    builtins.open = lambda *a, **k: (_ for _ in ()).throw(ImportError("open() sandbox'ta devre dışı."))
"""
).strip()


async def run_in_sandbox(code: str, timeout: float = 10.0) -> dict[str, Any]:
    """Kodu geçici dosyada sandbox içinde çalıştırır."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(SANDBOX_PREAMBLE + "\n\n")
        f.write(code)
        temp_path = f.name

    try:
        proc = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                sys.executable,
                temp_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ),
            timeout=timeout,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
        return {
            "returncode": proc.returncode,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
        }
    except asyncio.TimeoutError:
        if proc and proc.returncode is None:
            proc.kill()
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": "Zaman aşımı (timeout).",
        }
    finally:
        try:
            os.unlink(temp_path)
        except OSError:
            pass


# ──────────────────────────────
#  Araştırma yardımcıları
# ──────────────────────────────

async def _duckduckgo_search(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """DuckDuckGo HTML üzerinden arama yapar (resmi API olmadığında)."""
    results: list[dict[str, str]] = []
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            url = "https://html.duckduckgo.com/html/"
            resp = await client.post(url, data={"q": query, "kl": "en-us"})
            resp.raise_for_status()
            text = resp.text
            # Basit regex ile snippet çekimi
            snippets = re.findall(
                r'<a[^>]+class="result__a"[^>]*>(.*?)</a>.*?<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
                text,
                re.DOTALL,
            )
            for title, snippet in snippets[:max_results]:
                # HTML tag temizleme
                clean = re.sub(r"<[^>]+>", "", snippet).strip()
                results.append({"title": title, "snippet": clean})
    except Exception as exc:
        logger.warning("DuckDuckGo araması başarısız: %s", exc)
    return results


async def _github_search(query: str, max_results: int = 3) -> list[dict[str, str]]:
    """GitHub'da README ve örnek kod ara."""
    results: list[dict[str, str]] = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # README içinde arama
            url = (
                "https://api.github.com/search/repositories"
                f"?q={query.replace(' ', '+')}+in:readme+language:python"
                f"&sort=stars&order=desc&per_page={max_results}"
            )
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("items", []):
                    results.append(
                        {
                            "name": item.get("full_name", ""),
                            "url": item.get("html_url", ""),
                            "description": item.get("description", ""),
                        }
                    )
    except Exception as exc:
        logger.warning("GitHub araması başarısız: %s", exc)
    return results


async def _wikipedia_summary(query: str) -> str:
    """Wikipedia'dan kısa özet çek."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("extract", "")
    except Exception as exc:
        logger.warning("Wikipedia özet çekimi başarısız: %s", exc)
    return ""


# ──────────────────────────────
#  LLM Prompt yardımcıları
# ──────────────────────────────

def _build_generate_prompt(
    skill_name: str, description: str, research: ResearchResult
) -> str:
    snippets = "\n".join(f"- {s}" for s in research.snippets[:5])
    code_examples = "\n".join(
        f"\n### Örnek {i+1}\n```python\n{c[:1500]}\n```"
        for i, c in enumerate(research.code_examples[:3])
    )
    docs = "\n".join(f"- {d}" for d in research.docs[:5])

    prompt = textwrap.dedent(
        f"""\
        Sen güvenli Python kodu üreten bir AI asistansın.

        Görev: "{skill_name}" adında yeni bir araç/skill yaz.
        Amaç: {description}

        Araştırma bulguları:
        {snippets}

        Dokümanlar:
        {docs}

        Kod örnekleri:
        {code_examples}

        KURALLAR (KESİNLİKLE UYULMALI):
        1. Sadece PURE Python + math + json modüllerini kullan. os, subprocess, socket, urllib, eval, exec, compile, __import__ YOK.
        2. Fonksiyon async olmalı: `async def auto_{skill_name}(**kwargs) -> Any:`
        3. Fonksiyon docstring içermeli – giriş/çıkış açıklamalı.
        4. JSON schema üret (OpenAI function schema formatında).
        5. Hata yönetimi (try/except) olsun.
        6. Kod tek, bağımsız bir Python dosyası gibi olmalı.
        7. En alta test case'leri (dict list) bir değişkende: `_TESTS = [...]`
        8. YORUMSATIRLARI Türkçe olabilir, kod İngilizce.

        Çıktı formatı (JSON):
        {{
          "code": "Tam Python kodu burada (tek satır için \\n ile escape edilmiş)",
          "schema": {{...}},
          "tests": [{{"input": {{...}}, "expected": ...}}],
          "confidence": 0.0-1.0
        }}
        """
    )
    return prompt


def _build_analyze_prompt(objective: str, available_tools: list[str]) -> str:
    tools_str = ", ".join(available_tools) if available_tools else "(hiçbiri)"
    prompt = textwrap.dedent(
        f"""\
        Kullanıcı şu görevi istiyor: "{objective}"
        Mevcut araçlar: {tools_str}

        Bu görevi yerine getirmek için hangi yeni yetenek/araç eksik?
        JSON formatında yanıt ver:
        {{
          "missing_skill": "kısa yetenek adı",
          "required_inputs": ["input1", "input2"],
          "expected_output": "açıklama",
          "confidence": 0.0-1.0
        }}
        Eğer mevcut araçlar yeterliyse missing_skill boş string olsun.
        """
    )
    return prompt


# ──────────────────────────────
#  Ana Motor
# ──────────────────────────────

class AutoSkillGenerator:
    """Yeni araç/skill üreten ve test eden motor."""

    def __init__(
        self,
        llm_client: Any,
        tool_registry: Any,
        project_dir: str = ".",
    ):
        self.llm = llm_client
        self.registry = tool_registry
        self.project_dir = Path(project_dir)
        self.skills_dir = (
            self.project_dir / "turkish_jarvis" / "tools" / "auto_generated"
        )
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self.skills_dir / "auto_skills_index.json"

    # ── 1. İhtiyaç analizi ──────────────────────────────

    async def analyze_need(
        self, objective: str, available_tools: list[str]
    ) -> NeedAnalysis:
        """Hangi yetenek eksik? LLM'e sor."""
        prompt = _build_analyze_prompt(objective, available_tools)
        raw = await self._llm_chat(prompt)
        data = self._extract_json(raw)
        if not data:
            return NeedAnalysis(
                missing_skill="", required_inputs=[], expected_output="", confidence=0.0
            )
        return NeedAnalysis(
            missing_skill=data.get("missing_skill", ""),
            required_inputs=data.get("required_inputs", []),
            expected_output=data.get("expected_output", ""),
            confidence=float(data.get("confidence", 0.0)),
        )

    # ── 2. Araştırma ────────────────────────────────────

    async def research(self, skill_name: str, description: str) -> ResearchResult:
        """İnternetten veya GitHub'dan bilgi topla."""
        query = f"python {skill_name} {description}"
        ddgs = await _duckduckgo_search(query, max_results=5)
        gh = await _github_search(skill_name, max_results=3)
        wiki = await _wikipedia_summary(skill_name)

        snippets = [d["snippet"] for d in ddgs if d.get("snippet")]
        sources = [d.get("title", "") for d in ddgs]
        sources += [g.get("url", "") for g in gh]
        if wiki:
            snippets.append(wiki)
            sources.append("Wikipedia")

        # GitHub'dan örnek kod çekimi – basit README raw isteği
        code_examples: list[str] = []
        for repo in gh[:2]:
            raw_url = repo.get("url", "").replace(
                "github.com", "raw.githubusercontent.com"
            )
            if raw_url:
                readme_url = raw_url + "/master/README.md"
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        r = await client.get(readme_url)
                        if r.status_code == 200:
                            text = r.text
                            # Kod bloklarını çıkar
                            blocks = re.findall(
                                r"```python(.*?)```", text, re.DOTALL
                            )
                            code_examples.extend(b.strip() for b in blocks if b.strip())
                except Exception:
                    pass

        docs = [g.get("description", "") for g in gh if g.get("description")]

        return ResearchResult(
            snippets=snippets,
            code_examples=code_examples,
            docs=docs,
            sources=sources,
        )

    # ── 3. Kod üretimi ──────────────────────────────────

    async def generate_code(
        self, skill_name: str, description: str, research: ResearchResult
    ) -> GeneratedSkill:
        """LLM ile Python fonksiyonu üret."""
        prompt = _build_generate_prompt(skill_name, description, research)
        raw = await self._llm_chat(prompt)
        data = self._extract_json(raw)
        if not data:
            raise RuntimeError("LLM JSON çıktısı üretemedi.")

        code = data.get("code", "")
        if not code:
            raise RuntimeError("LLM kod üretemedi.")

        # Güvenlik kontrolü
        self._security_check(code)

        # AST syntax kontrolü
        try:
            ast.parse(code)
        except SyntaxError as exc:
            raise RuntimeError(f"Üretilen kod syntax hatası: {exc}") from exc

        schema = data.get("schema", {})
        tests = data.get("tests", [])
        confidence = float(data.get("confidence", 0.5))

        # Test dict'lerini normalize et
        normalized_tests: list[dict] = []
        for t in tests:
            if isinstance(t, dict) and "input" in t:
                normalized_tests.append(t)

        return GeneratedSkill(
            name=skill_name,
            code=code,
            schema=schema,
            tests=normalized_tests,
            research_sources=research.sources,
            confidence=confidence,
        )

    # ── 4. Sandbox testi ────────────────────────────────

    async def test_skill(
        self, skill: GeneratedSkill, max_attempts: int = 3
    ) -> TestResult:
        """Sandbox içinde test et."""
        code = skill.code
        tests = skill.tests
        all_outputs: list[str] = []
        total_err: str | None = None
        passed = False
        start = asyncio.get_event_loop().time()

        # Temel syntax / import kontrolü
        self._security_check(code)

        for attempt in range(1, max_attempts + 1):
            # Test wrapper oluştur
            wrapper = self._build_test_wrapper(code, tests)
            result = await run_in_sandbox(wrapper, timeout=10.0)
            elapsed = asyncio.get_event_loop().time() - start

            stdout = result.get("stdout", "")
            stderr = result.get("stderr", "")
            rc = result.get("returncode", -1)

            all_outputs.append(f"--- Deneme {attempt} ---\n{stdout}\n{stderr}")

            if rc == 0 and "ALL_TESTS_PASSED" in stdout:
                passed = True
                total_err = None
                break
            total_err = stderr or f"Return code: {rc}"

            if attempt < max_attempts:
                # Hata mesajını LLM'e göndererek düzeltme talep et
                fix_prompt = self._build_fix_prompt(skill, stderr)
                fix_raw = await self._llm_chat(fix_prompt)
                fix_data = self._extract_json(fix_raw)
                if fix_data and fix_data.get("code"):
                    new_code = fix_data["code"]
                    self._security_check(new_code)
                    try:
                        ast.parse(new_code)
                        skill.code = new_code
                        code = new_code
                    except SyntaxError:
                        pass

        elapsed = asyncio.get_event_loop().time() - start
        return TestResult(
            passed=passed,
            output="\n".join(all_outputs),
            error=total_err,
            execution_time=elapsed,
        )

    # ── 5. Kalıcı kayıt ─────────────────────────────────

    async def register_skill(self, skill: GeneratedSkill) -> bool:
        """Başarılı skill'i kalıcı kaydet."""
        safe_name = re.sub(r"[^a-zA-Z0-9_]+", "_", skill.name).strip("_")
        if not safe_name:
            safe_name = "auto_skill"
        file_name = f"auto_{safe_name}.py"
        file_path = self.skills_dir / file_name

        # Kodu dosyaya yaz
        header = textwrap.dedent(
            f"""\
            # Auto-generated skill: {skill.name}
            # Confidence: {skill.confidence:.2f}
            # Generated at: {skill.generated_at.isoformat()}
            # Sources: {', '.join(skill.research_sources)}

            """
        )
        file_path.write_text(header + skill.code, encoding="utf-8")

        # Registry'ye dinamik yükle
        try:
            spec = importlib.util.spec_from_file_location(
                f"turkish_jarvis.tools.auto_generated.auto_{safe_name}",
                str(file_path),
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                func_name = f"auto_{safe_name}"
                if hasattr(module, func_name):
                    tool_func = getattr(module, func_name)
                    if callable(tool_func) and self.registry:
                        self.registry.register(
                            name=func_name,
                            func=tool_func,
                            schema=skill.schema,
                            source="auto_generated",
                        )
                        logger.info("Skill '%s' registry'ye eklendi.", func_name)
        except Exception as exc:
            logger.warning("Skill registry eklenemedi: %s", exc)

        # Index JSON güncelle
        index: list[dict] = []
        if self._index_path.exists():
            try:
                index = json.loads(self._index_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                index = []

        index.append(
            {
                "name": skill.name,
                "file": str(file_path.relative_to(self.project_dir)),
                "schema": skill.schema,
                "confidence": skill.confidence,
                "generated_at": skill.generated_at.isoformat(),
                "sources": skill.research_sources,
                "hash": hashlib.sha256(skill.code.encode()).hexdigest()[:16],
            }
        )
        self._index_path.write_text(
            json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        return True

    # ── 6. Tam pipeline ─────────────────────────────────

    async def acquire_skill(self, objective: str) -> SkillAcquisitionResult:
        """Tam pipeline: ihtiyaç → araştırma → üretim → test → kayıt."""
        available = []
        if self.registry and hasattr(self.registry, "list_tools"):
            try:
                available = self.registry.list_tools()
            except Exception:
                pass

        need = await self.analyze_need(objective, available)
        if not need.missing_skill:
            return SkillAcquisitionResult(
                success=True,
                skill_name=None,
                message="Mevcut araçlar bu görevi yerine getirmeye yeterli.",
            )

        skill_name = need.missing_skill
        logger.info("Eksik yetenek tespit edildi: %s", skill_name)

        research = await self.research(skill_name, need.expected_output)
        logger.info("Araştırma tamamlandı. Kaynaklar: %d", len(research.sources))

        try:
            skill = await self.generate_code(skill_name, need.expected_output, research)
        except RuntimeError as exc:
            return SkillAcquisitionResult(
                success=False, skill_name=skill_name, message=f"Kod üretimi başarısız: {exc}"
            )

        logger.info("Kod üretildi. Güven: %.2f", skill.confidence)

        test_result = await self.test_skill(skill)
        if not test_result.passed:
            return SkillAcquisitionResult(
                success=False,
                skill_name=skill_name,
                message=f"Test başarısız: {test_result.error}",
                test_result=test_result,
            )

        logger.info("Test başarılı. Kaydediliyor...")
        await self.register_skill(skill)

        return SkillAcquisitionResult(
            success=True,
            skill_name=skill.name,
            message=f"'{skill.name}' başarıyla edinildi ve kaydedildi.",
            test_result=test_result,
        )

    # ── Dahili yardımcılar ──────────────────────────────

    async def _llm_chat(self, prompt: str) -> str:
        """LLM istemci abstraction."""
        if self.llm is None:
            return "{}"
        # Basit interface: .complete() veya .chat()
        if hasattr(self.llm, "complete"):
            return await self.llm.complete(prompt)
        if hasattr(self.llm, "chat"):
            return await self.llm.chat(prompt)
        raise RuntimeError("LLM client uyumlu arayüz bulunamadı.")

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any] | None:
        """Metinden JSON bloğu çıkar."""
        # ```json ... ```
        m = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
        # Ham JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # { ... } ara
        m2 = re.search(r"(\{.*\})", text, re.DOTALL)
        if m2:
            try:
                return json.loads(m2.group(1))
            except json.JSONDecodeError:
                pass
        return None

    @staticmethod
    def _security_check(code: str) -> None:
        """AST ile yasaklı yapıları kontrol et."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            raise SecurityError("Kod parse edilemiyor (syntax hatası).")
        checker = SecurityChecker()
        checker.visit(tree)
        if checker.violations:
            raise SecurityError("; ".join(checker.violations))

    @staticmethod
    def _build_test_wrapper(code: str, tests: list[dict]) -> str:
        """Test case'leri çalıştıran wrapper kod üret."""
        wrapper = textwrap.dedent(
            """\
            import asyncio, json, traceback

            {code}

            async def _run_tests():
                tests = {tests}
                passed = 0
                failed = 0
                func = globals()["{func_name}"]
                for i, t in enumerate(tests):
                    try:
                        inp = t.get("input", {{}})
                        expected = t.get("expected")
                        result = await func(**inp)
                        if result == expected:
                            passed += 1
                        else:
                            failed += 1
                            print(f"TEST_FAIL {{i}}: expected={{expected}} got={{result}}")
                    except Exception as e:
                        failed += 1
                        print(f"TEST_ERR {{i}}: {{e}}")
                        traceback.print_exc()
                if failed == 0 and len(tests) > 0:
                    print("ALL_TESTS_PASSED")
                elif len(tests) == 0:
                    print("NO_TESTS_DEFINED")
                else:
                    print(f"TESTS: {{passed}} passed, {{failed}} failed")

            if asyncio.iscoroutinefunction(_run_tests):
                asyncio.run(_run_tests())
            else:
                _run_tests()
            """
        )
        # Fonksiyon adını tespit et (ilk async def)
        m = re.search(r"async\s+def\s+(auto_\w+)", code)
        func_name = m.group(1) if m else "auto_unknown"
        return wrapper.format(code=code, tests=json.dumps(tests), func_name=func_name)

    @staticmethod
    def _build_fix_prompt(skill: GeneratedSkill, error: str) -> str:
        return textwrap.dedent(
            f"""\
            Aşağıdaki kod sandbox testinde hata verdi.
            Hata: {error}

            Kod:
            ```python
            {skill.code}
            ```

            Testler:
            ```json
            {json.dumps(skill.tests, indent=2)}
            ```

            Lütfen düzeltilmiş kodu JSON formatında döndür:
            {{"code": "...", "confidence": 0.0-1.0}}
            """
        )


# ──────────────────────────────
#  Registry helper (minimal)
# ──────────────────────────────

class ToolRegistry:
    """Skill kayıtlarını tutan minimal registry (örnek)."""

    def __init__(self) -> None:
        self._tools: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        func: Callable[..., Any],
        schema: dict[str, Any],
        source: str = "manual",
    ) -> None:
        self._tools[name] = {
            "func": func,
            "schema": schema,
            "source": source,
        }
        logger.info("Tool '%s' kaydedildi (kaynak: %s).", name, source)

    def get(self, name: str) -> dict[str, Any] | None:
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())


# ──────────────────────────────
#  Convenience
# ──────────────────────────────

async def main() -> None:
    """CLI quick-test (örnek)."""
    # Basit mock LLM
    class MockLLM:
        async def complete(self, prompt: str) -> str:
            # Gerçek uygulamada burada OpenAI/Anthropic çağrısı olur
            return json.dumps(
                {
                    "missing_skill": "to_upper",
                    "required_inputs": ["text"],
                    "expected_output": "Büyük harfli metin",
                    "confidence": 0.95,
                }
            )

    registry = ToolRegistry()
    gen = AutoSkillGenerator(MockLLM(), registry, project_dir=".")
    result = await gen.acquire_skill("metni büyük harfe çevir")
    print("Sonuç:", result)


if __name__ == "__main__":
    asyncio.run(main())
