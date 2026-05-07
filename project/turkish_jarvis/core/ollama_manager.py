"""Ollama Process Manager — Subprocess control, port management, health monitoring."""

import os
import subprocess
import socket
import time
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("jarvis.ollama_manager")


class OllamaProcessManager:
    """Ollama'yı subprocess olarak yönetir.

    - Sistemde zaten çalışan bir Ollama varsa ona bağlanır.
    - Yoksa ``11434-11500`` aralığında boş bir port bularak
      ``ollama serve`` başlatır.
    - Model yükleme/boşaltma, sağlık kontrolü ve URL üretimi sunar.
    """

    def __init__(self, base_port: int = 11434, max_port: int = 11500):
        self.base_port = base_port
        self.max_port = max_port
        self.current_port: Optional[int] = None
        self.process: Optional[subprocess.Popen] = None
        self.models_loaded: list[str] = []

    # ------------------------------------------------------------------
    # Port utilities
    # ------------------------------------------------------------------

    def _is_port_in_use(self, port: int) -> bool:
        """Belirtilen *port* localhost üzerinde dinleniyor mu?"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("localhost", port)) == 0

    def find_free_port(self) -> int:
        """``11434-11500`` aralığında boş bir port döndür."""
        for port in range(self.base_port, self.max_port + 1):
            if not self._is_port_in_use(port):
                return port
        raise RuntimeError(f"{self.base_port}-{self.max_port} aralığında boş port bulunamadı")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self, port: Optional[int] = None) -> int:
        """Ollama'yı başlat veya mevcut olana bağlan.

        1. Sistemde ``ollama serve`` çalışıyorsa → port tespit et, bağlan.
        2. Çalışmıyorsa → boş port bul, yeni süreç başlat, sağlık bekle.

        Args:
            port: Belirli bir port ile başlatmak isterseniz girin.

        Returns:
            Kullanılan port numarası.
        """
        # Mevcut sistem Ollama'sı var mı?
        if self._is_ollama_running():
            self.current_port = self._detect_ollama_port()
            logger.info("✅ Sistem Ollama'sı tespit edildi: port %d", self.current_port)
            return self.current_port

        # Kendi sürecimizi başlat
        if port is None:
            port = self.find_free_port()

        env = os.environ.copy()
        env["OLLAMA_HOST"] = f"0.0.0.0:{port}"

        self.process = subprocess.Popen(
            ["ollama", "serve"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.current_port = port

        self._wait_for_health(port)
        logger.info("✅ Ollama başlatıldı: port %d", port)
        return port

    def stop(self) -> None:
        """Bizim başlattığımız Ollama sürecini düzgünce durdur."""
        if self.process is None:
            logger.debug("Duracak yerel süreç yok.")
            return

        self.process.terminate()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            logger.warning("Ollama 10 sn içinde kapanmadı, kill gönderiliyor.")
            self.process.kill()
            self.process.wait()
        finally:
            self.process = None
            logger.info("🛑 Ollama durduruldu")

    def restart(self) -> int:
        """Durdur ve yeniden başlat."""
        self.stop()
        return self.start()

    def is_running(self) -> bool:
        """Ollama çalışıyor mu? (yerel süreç veya sistem süreci)"""
        if self.process is not None:
            return self.process.poll() is None
        return self._is_ollama_running()

    # ------------------------------------------------------------------
    # Model management
    # ------------------------------------------------------------------

    def get_models(self) -> list[str]:
        """``ollama list`` çıktısından model isimlerini döndür."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            lines = result.stdout.strip().split("\n")[1:]  # skip header
            return [line.split()[0] for line in lines if line.strip()]
        except Exception as exc:
            logger.warning("Model listesi alınamadı: %s", exc)
            return []

    def load_model(self, model: str) -> bool:
        """*model*'i belleğe yükle (``ollama run``)."""
        try:
            subprocess.run(
                ["ollama", "run", model, "--nowait"],
                capture_output=True,
                timeout=300,
            )
            if model not in self.models_loaded:
                self.models_loaded.append(model)
            return True
        except Exception as exc:
            logger.error("Model yükleme başarısız (%s): %s", model, exc)
            return False

    def unload_model(self, model: str) -> bool:
        """*model*'i bellekten boşalt (``ollama rm``)."""
        try:
            subprocess.run(
                ["ollama", "rm", model],
                capture_output=True,
                timeout=60,
            )
            self.models_loaded = [m for m in self.models_loaded if m != model]
            return True
        except Exception as exc:
            logger.error("Model boşaltma başarısız (%s): %s", model, exc)
            return False

    # ------------------------------------------------------------------
    # URL & health
    # ------------------------------------------------------------------

    def get_url(self) -> str:
        """Ollama API URL'si."""
        if self.current_port:
            return f"http://localhost:{self.current_port}"
        return "http://localhost:11434"

    def health_check(self) -> dict:
        """/api/tags endpoint'i üzerinden sağlık kontrolü."""
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover
            return {"status": "unhealthy", "error": f"httpx eksik: {exc}"}

        try:
            resp = httpx.get(f"{self.get_url()}/api/tags", timeout=5.0)
            data = resp.json()
            return {
                "status": "healthy" if resp.status_code == 200 else "unhealthy",
                "models": len(data.get("models", [])),
            }
        except Exception as exc:
            return {"status": "unhealthy", "error": str(exc)}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _is_ollama_running(self) -> bool:
        """Sistemde ``ollama`` süreci var mı?"""
        try:
            import psutil
            for proc in psutil.process_iter(["name", "cmdline"]):
                info = proc.info
                if info.get("name") == "ollama":
                    return True
                cmdline = info.get("cmdline")
                if cmdline and any("ollama" in str(arg) for arg in cmdline):
                    return True
            return False
        except ImportError:
            # Fallback: port kontrolü
            return self._is_port_in_use(self.base_port)

    def _detect_ollama_port(self) -> int:
        """Çalışan Ollama'nın portunu bul."""
        for port in range(self.base_port, self.max_port + 1):
            if self._is_port_in_use(port):
                try:
                    import httpx
                    resp = httpx.get(f"http://localhost:{port}/api/tags", timeout=2.0)
                    if resp.status_code == 200:
                        return port
                except Exception:
                    continue
        return self.base_port  # default

    def _wait_for_health(self, port: int, timeout: int = 60) -> None:
        """Ollama hazır olana kadar bekle."""
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(f"httpx gerekli: {exc}")

        start = time.time()
        url = f"http://localhost:{port}/api/tags"
        while time.time() - start < timeout:
            try:
                resp = httpx.get(url, timeout=2.0)
                if resp.status_code == 200:
                    return
            except Exception:
                pass
            time.sleep(1)

        raise TimeoutError(f"Ollama port {port} üzerinde {timeout}s içinde hazır olmadı")
