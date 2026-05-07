"""EvaluatorAgent — Model çıktısı değerlendirme ve puanlama."""

from typing import Any, Dict
from ..base_agent import BaseAgent


class EvaluatorAgent(BaseAgent):
    """Model çıktısı değerlendirme ve puanlama."""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(
            name="EvaluatorAgent",
            role="evaluator",
            description="Model çıktısı değerlendirme ve puanlama.",
            config=config,
        )

    async def run(self, payload: Any) -> Any:
        self.status = "running"
        self.log(f"{self.role} görevi başlatıldı: {payload}")
        # TODO: Council-specific logic
        result = {"agent": self.name, "input": payload, "status": "ok"}
        self.status = "idle"
        return result
