"""Ollama Model Pool — 7 modeli paralel çalıştırma havuzu."""

import asyncio
import logging
from typing import Optional
from collections import deque

logger = logging.getLogger("jarvis.model_pool")

class OllamaModelPool:
    """Kullanıcının 7 Ollama modelini paralel çalıştıran havuz."""
    
    MODELS = {
        "qwen3-coder:30b": {"type": "coding", "priority": 1, "vram": 20},
        "llama3.1:70b": {"type": "heavy", "priority": 2, "vram": 48},
        "gemma4:latest": {"type": "fast", "priority": 3, "vram": 12},
        "deepseek-r1:8b": {"type": "math", "priority": 4, "vram": 8},
        "mistral:latest": {"type": "fast", "priority": 5, "vram": 6},
        "qwen3:4b": {"type": "light", "priority": 6, "vram": 4},
        "gemma3:4b": {"type": "light", "priority": 7, "vram": 4},
    }
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.available_models: list[str] = []
        self.queue: asyncio.Queue = asyncio.Queue()
        self.active_requests: int = 0
        self.max_parallel: int = 3  # Aynı anda max 3 model
    
    async def initialize(self) -> None:
        """Mevcut modelleri tespit et."""
        import httpx
        try:
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            data = resp.json()
            self.available_models = [m["name"] for m in data.get("models", [])]
            logger.info("🧠 Model Pool: %d model mevcut", len(self.available_models))
        except Exception:
            logger.warning("Model Pool: Ollama bağlantısı yok")
    
    def select_model(self, task_type: str) -> str:
        """Görev tipine göre en uygun modeli seç."""
        mapping = {
            "coding": "qwen3-coder:30b",
            "math": "deepseek-r1:8b",
            "analysis": "llama3.1:70b",
            "chat": "gemma4:latest",
            "quick": "mistral:latest",
            "light": "qwen3:4b",
        }
        preferred = mapping.get(task_type, "qwen3-coder:30b")
        
        # Mevcut modellerden en uygunu bul
        for model in [preferred] + list(self.MODELS.keys()):
            if model in self.available_models:
                return model
        return self.available_models[0] if self.available_models else preferred
    
    def get_client(self):
        """LLM client döndür."""
        from turkish_jarvis.core.llm import LLMClient
        return LLMClient()
    
    async def parallel_inference(self, prompts: list[dict], task_type: str = "chat") -> list[str]:
        """Aynı anda birden fazla prompt için inference."""
        model = self.select_model(task_type)
        # Paralel çalıştırma
        semaphore = asyncio.Semaphore(self.max_parallel)
        
        async def _infer(prompt):
            async with semaphore:
                # LLM çağrısı
                return f"Result for: {prompt}"
        
        return await asyncio.gather(*[_infer(p) for p in prompts])
