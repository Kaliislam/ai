from turkish_jarvis.agents.base_agent import BaseAgent


class TrainerAgent(BaseAgent):
    """Egitmen ajani — egitim materyali ve ogrenme yollari."""
    def __init__(self):
        super().__init__("Trainer", "Trainer", "Operations", "qwen3-coder:30b")
        self.skills = ["course_design", "onboarding", "knowledge_assessment", "certification"]

    async def _process(self, task, llm_client=None):
        # Egitim mantigi
        subject = task.get('subject', '')
        return {'curriculum': 'designed', 'subject': subject, 'modules': []}
