from turkish_jarvis.agents.base_agent import BaseAgent


class CarManagerAgent(BaseAgent):
    """Araç Yöneticisi — vehicle_maintenance, fuel, service, reminders."""

    def __init__(self):
        super().__init__("carmanager", "Araç Yöneticisi", "Personal", "gemma4:latest")
        self.skills = ["vehicle_maintenance", "fuel", "service", "reminders"]

    async def _process(self, task, llm_client=None):
        return {"agent": "carmanager", "processed": task.get("count", 0)}
