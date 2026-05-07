"""PriorityAgent — Görev önceliklendirme ve sıralama."""

from typing import Any, Dict
from ..base_agent import BaseAgent


class PriorityAgent(BaseAgent):
    """Görev önceliklendirme ve sıralama."""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(
            name="PriorityAgent",
            role="priority",
            description="Görev önceliklendirme ve sıralama.",
            config=config,
        )

    async def run(self, payload: Any) -> Any:
        self.status = "running"
        self.log(f"{self.role} görevi başlatıldı: {payload}")
        # TODO: Council-specific logic
        result = {"agent": self.name, "input": payload, "status": "ok"}
        self.status = "idle"
        return result
