from turkish_jarvis.agents.base_agent import BaseAgent


class ChiefHumanResourcesOfficer(BaseAgent):
    """İnsan kaynaklari şefi -- ekip kurma, yetenek yönetimi ve kültür."""

    def __init__(self):
        super().__init__("CHRO", "Chief HR Officer", "Executive", "llama3.1:70b")
        self.skills = ["recruiting", "talent_management", "culture", "training"]

    async def _process(self, task, llm_client=None):
        return {"action": "hr_action", "focus": task.get("people_topic")}
