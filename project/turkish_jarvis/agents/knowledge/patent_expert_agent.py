from turkish_jarvis.agents.base_agent import BaseAgent


class PatentExpertAgent(BaseAgent):
    """Patent Uzmanı — patent_search, prior_art, filings, claims."""

    def __init__(self):
        super().__init__("patentexpert", "Patent Uzmanı", "Knowledge", "gemma4:latest")
        self.skills = ["patent_search", "prior_art", "filings", "claims"]

    async def _process(self, task, llm_client=None):
        return {"agent": "patentexpert", "processed": task.get("count", 0)}
