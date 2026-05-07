from turkish_jarvis.agents.base_agent import BaseAgent


class ResearchExpertAgent(BaseAgent):
    """Araştırma Uzmanı — research_methodology, literature, review, synthesis."""

    def __init__(self):
        super().__init__("researchexpert", "Araştırma Uzmanı", "Knowledge", "gemma4:latest")
        self.skills = ["research_methodology", "literature", "review", "synthesis"]

    async def _process(self, task, llm_client=None):
        return {"agent": "researchexpert", "processed": task.get("count", 0)}
