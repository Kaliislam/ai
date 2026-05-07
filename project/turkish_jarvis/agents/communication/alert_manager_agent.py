from turkish_jarvis.agents.base_agent import BaseAgent


class AlertManagerAgent(BaseAgent):
    """Uyarı Yöneticisi — alerts, escalation, thresholds, critical_events."""

    def __init__(self):
        super().__init__("alertmanager", "Uyarı Yöneticisi", "Communication", "gemma4:latest")
        self.skills = ["alerts", "escalation", "thresholds", "critical_events"]

    async def _process(self, task, llm_client=None):
        return {"agent": "alertmanager", "processed": task.get("count", 0)}
