from turkish_jarvis.agents.base_agent import BaseAgent


class PetManagerAgent(BaseAgent):
    """Evcil Hayvan Yöneticisi — pet_care, feeding, schedules, vet_appointments."""

    def __init__(self):
        super().__init__("petmanager", "Evcil Hayvan Yöneticisi", "Personal", "gemma4:latest")
        self.skills = ["pet_care", "feeding", "schedules", "vet_appointments"]

    async def _process(self, task, llm_client=None):
        return {"agent": "petmanager", "processed": task.get("count", 0)}
