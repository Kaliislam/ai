from turkish_jarvis.agents.base_agent import BaseAgent


class HealthManagerAgent(BaseAgent):
    """Sağlık Yöneticisi — health_tracking, vitals, appointments, wellness."""

    def __init__(self):
        super().__init__("healthmanager", "Sağlık Yöneticisi", "Personal", "gemma4:latest")
        self.skills = ["health_tracking", "vitals", "appointments", "wellness"]

    async def _process(self, task, llm_client=None):
        return {"agent": "healthmanager", "processed": task.get("count", 0)}
