from turkish_jarvis.agents.base_agent import BaseAgent


class TechnicalWriterAgent(BaseAgent):
    """Teknik yazar ajani — dokumantasyon ve icerik uretimi."""
    def __init__(self):
        super().__init__("TechnicalWriter", "Technical Writer", "Operations", "qwen3-coder:30b")
        self.skills = ["documentation", "api_guides", "release_notes", "knowledge_base"]

    async def _process(self, task, llm_client=None):
        # Dokumantasyon mantigi
        topic = task.get('topic', 'general')
        return {'doc': 'written', 'topic': topic, 'sections': []}
