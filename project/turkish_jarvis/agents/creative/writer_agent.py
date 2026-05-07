"""Writer Agent — metin üretimi ve düzenleme."""

from turkish_jarvis.agents.base_agent import BaseAgent

class WriterAgent(BaseAgent):
    """Yazar ajanı — metin üretimi ve düzenleme."""
    def __init__(self):
        super().__init__("Writer", "Writer", "Creative", "gemma4:latest")
        self.skills = ["writing", "editing", "storytelling", "copywriting", "content creation"]

    async def _process(self, task, llm_client=None):
        return {"content": "Processed by Writer", "type": task.get("type", "generic")}
