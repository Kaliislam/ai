"""Capacity Agent — Kapasite planlayıcı."""

from turkish_jarvis.agents.base_agent import BaseAgent


class CapacityAgent(BaseAgent):
    """Kapasite planlayıcı — kaynak tahmini, ölçeklendirme planı."""

    def __init__(self):
        super().__init__("Capacity", "Capacity Planner", "Systems", "qwen3-coder:30b")
        self.skills = ["forecasting", "scaling", "resource_plan", "trend"]

    async def _process(self, task, llm_client=None):
        return {"capacity_forecast": "updated", "action_taken": task.get("action")}
