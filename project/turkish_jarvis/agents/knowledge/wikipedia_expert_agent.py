from turkish_jarvis.agents.base_agent import BaseAgent


class WikipediaExpertAgent(BaseAgent):
    """Wikipedia Uzmanı — wikipedia_search, summarization, fact_checking."""

    def __init__(self):
        super().__init__("wikipediaexpert", "Wikipedia Uzmanı", "Knowledge", "gemma4:latest")
        self.skills = ["wikipedia_search", "summarization", "fact_checking"]

    async def _process(self, task, llm_client=None):
        return {"agent": "wikipediaexpert", "processed": task.get("count", 0)}
