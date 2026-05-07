from turkish_jarvis.agents.base_agent import BaseAgent


class NewsExpertAgent(BaseAgent):
    """Haber Uzmanı — news_aggregation, trending, topics, source_verification."""

    def __init__(self):
        super().__init__("newsexpert", "Haber Uzmanı", "Knowledge", "gemma4:latest")
        self.skills = ["news_aggregation", "trending", "topics", "source_verification"]

    async def _process(self, task, llm_client=None):
        return {"agent": "newsexpert", "processed": task.get("count", 0)}
