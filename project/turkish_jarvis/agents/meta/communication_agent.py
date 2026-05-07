"""CommunicationAgent — Ajanlar arası iletişim ve mesaj yönetimi."""

from typing import Any, Dict
from ..base_agent import BaseAgent


class CommunicationAgent(BaseAgent):
    """Ajanlar arası iletişim ve mesaj yönetimi."""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(
            name="CommunicationAgent",
            role="communication",
            description="Ajanlar arası iletişim ve mesaj yönetimi.",
            config=config,
        )

    async def run(self, payload: Any) -> Any:
        self.status = "running"
        self.log(f"{self.role} görevi başlatıldı: {payload}")
        # TODO: Council-specific logic
        result = {"agent": self.name, "input": payload, "status": "ok"}
        self.status = "idle"
        return result
