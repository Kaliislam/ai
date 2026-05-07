from turkish_jarvis.agents.base_agent import BaseAgent


class BookExpertAgent(BaseAgent):
    """Kitap Uzmanı — book_recommendations, summaries, reviews, genres."""

    def __init__(self):
        super().__init__("bookexpert", "Kitap Uzmanı", "Knowledge", "gemma4:latest")
        self.skills = ["book_recommendations", "summaries", "reviews", "genres"]

    async def _process(self, task, llm_client=None):
        return {"agent": "bookexpert", "processed": task.get("count", 0)}
