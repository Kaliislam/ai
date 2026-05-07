from turkish_jarvis.agents.base_agent import BaseAgent


class MedicalExpertAgent(BaseAgent):
    """Tıbbi Uzman — medical_research, symptoms, drugs, evidence."""

    def __init__(self):
        super().__init__("medicalexpert", "Tıbbi Uzman", "Knowledge", "gemma4:latest")
        self.skills = ["medical_research", "symptoms", "drugs", "evidence"]

    async def _process(self, task, llm_client=None):
        return {"agent": "medicalexpert", "processed": task.get("count", 0)}
