"""TokenizerAgent — Metin tokenizasyonu ve uzunluk yönetimi."""

from typing import Any, Dict
from ..base_agent import BaseAgent


class TokenizerAgent(BaseAgent):
    """Metin tokenizasyonu ve uzunluk yönetimi."""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(
            name="TokenizerAgent",
            role="tokenizer",
            description="Metin tokenizasyonu ve uzunluk yönetimi.",
            config=config,
        )

    async def run(self, payload: Any) -> Any:
        self.status = "running"
        self.log(f"{self.role} görevi başlatıldı: {payload}")
        # TODO: Council-specific logic
        result = {"agent": self.name, "input": payload, "status": "ok"}
        self.status = "idle"
        return result
