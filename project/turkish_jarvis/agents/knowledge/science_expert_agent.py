from turkish_jarvis.agents.base_agent import BaseAgent


class ScienceExpertAgent(BaseAgent):
    """Bilim Uzmanı — scientific_research, discoveries, experiments, peer_review."""

    def __init__(self):
        super().__init__("scienceexpert", "Bilim Uzmanı", "Knowledge", "gemma4:latest")
        self.skills = ["scientific_research", "discoveries", "experiments", "peer_review"]

    async def _process(self, task, llm_client=None):
        return {"agent": "scienceexpert", "processed": task.get("count", 0)}
