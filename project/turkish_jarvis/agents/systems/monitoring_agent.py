"""Monitoring Agent — İzleme ajanı."""

from turkish_jarvis.agents.base_agent import BaseAgent


class MonitoringAgent(BaseAgent):
    """İzleme ajanı — metrik toplama, uyarı, dashboard."""

    def __init__(self):
        super().__init__("Monitoring", "Monitoring Engineer", "Systems", "qwen3-coder:30b")
        self.skills = ["metrics", "alerting", "dashboards", "apm"]

    async def _process(self, task, llm_client=None):
        return {"metrics": "collected", "action_taken": task.get("action")}
