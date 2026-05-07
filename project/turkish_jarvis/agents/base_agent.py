"""Base Agent class — tüm ajanların temel sınıfı."""
from typing import Any, Optional
import logging

logger = logging.getLogger("jarvis.agents")


class BaseAgent:
    """Jarvis CEO'ya itaat eden tüm ajanların temel sınıfı."""

    def __init__(self, name: str, role: str, department: str,
                 model_preference: str = "qwen3-coder:30b"):
        self.name = name
        self.role = role
        self.department = department
        self.model_preference = model_preference
        self.status = "idle"  # idle | working | completed | error
        self.report_to = "Jarvis"  # CEO
        self.skills: list[str] = []
        self.task_history: list[dict] = []

    async def execute_task(self, task: dict, llm_client=None) -> dict:
        """CEO'dan gelen görevi yürüt."""
        self.status = "working"
        try:
            result = await self._process(task, llm_client)
            self.status = "completed"
            self.task_history.append({"task": task, "result": result, "status": "success"})
            return {"agent": self.name, "status": "success", "result": result}
        except Exception as exc:
            self.status = "error"
            logger.error(f"{self.name} hata: {exc}")
            return {"agent": self.name, "status": "error", "error": str(exc)}

    async def _process(self, task: dict, llm_client=None) -> Any:
        """Alt sınıflar override eder."""
        return f"{self.name} görevi tamamladı: {task}"

    def report_status(self) -> dict:
        """CEO'ya durum raporu."""
        return {
            "name": self.name,
            "role": self.role,
            "department": self.department,
            "status": self.status,
            "tasks_completed": len(self.task_history),
            "model": self.model_preference,
        }
