"""Editor Agent — metin düzenleme, proofreading."""

from turkish_jarvis.agents.base_agent import BaseAgent

class EditorAgent(BaseAgent):
    """Editör ajanı — metin düzenleme, proofreading."""
    def __init__(self):
        super().__init__("Editor", "Editor", "Creative", "gemma4:latest")
        self.skills = ["proofreading", "grammar", "style correction", "publishing", "content review"]

    async def _process(self, task, llm_client=None):
        return {"content": "Processed by Editor", "type": task.get("type", "generic")}
