"""ModelSelectorAgent — Göreve en uygun LLM modelini seçer."""

from typing import Any, Dict
from ..base_agent import BaseAgent


class ModelSelectorAgent(BaseAgent):
    """Göreve en uygun LLM modelini seçer."""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(
            name="ModelSelectorAgent",
            role="model selector",
            description="Göreve en uygun LLM modelini seçer.",
            config=config,
        )

    async def run(self, payload: Any) -> Any:
        self.status = "running"
        self.log(f"{self.role} görevi başlatıldı: {payload}")
        # TODO: Council-specific logic
        result = {"agent": self.name, "input": payload, "status": "ok"}
        self.status = "idle"
        return result
