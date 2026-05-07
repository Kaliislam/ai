from turkish_jarvis.agents.base_agent import BaseAgent


class GardenManagerAgent(BaseAgent):
    """Bahçe Yöneticisi — gardening, plants, watering, schedules, tips."""

    def __init__(self):
        super().__init__("gardenmanager", "Bahçe Yöneticisi", "Personal", "gemma4:latest")
        self.skills = ["gardening", "plants", "watering", "schedules", "tips"]

    async def _process(self, task, llm_client=None):
        return {"agent": "gardenmanager", "processed": task.get("count", 0)}
