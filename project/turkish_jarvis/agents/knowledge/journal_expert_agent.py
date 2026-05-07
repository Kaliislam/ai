from turkish_jarvis.agents.base_agent import BaseAgent


class JournalExpertAgent(BaseAgent):
    """Dergi Uzmanı — journal_search, articles, impact_factors, subscriptions."""

    def __init__(self):
        super().__init__("journalexpert", "Dergi Uzmanı", "Knowledge", "gemma4:latest")
        self.skills = ["journal_search", "articles", "impact_factors", "subscriptions"]

    async def _process(self, task, llm_client=None):
        return {"agent": "journalexpert", "processed": task.get("count", 0)}
