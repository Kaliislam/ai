from turkish_jarvis.agents.base_agent import BaseAgent


class LawExpertAgent(BaseAgent):
    """Hukuk Uzmanı — legal_research, statutes, case_law, interpretation."""

    def __init__(self):
        super().__init__("lawexpert", "Hukuk Uzmanı", "Knowledge", "gemma4:latest")
        self.skills = ["legal_research", "statutes", "case_law", "interpretation"]

    async def _process(self, task, llm_client=None):
        return {"agent": "lawexpert", "processed": task.get("count", 0)}
