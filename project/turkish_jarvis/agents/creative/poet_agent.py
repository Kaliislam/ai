"""Poet Agent — şiir yazımı ve edebi metin."""

from turkish_jarvis.agents.base_agent import BaseAgent

class PoetAgent(BaseAgent):
    """Şair ajanı — şiir yazımı ve edebi metin."""
    def __init__(self):
        super().__init__("Poet", "Poet", "Creative", "gemma4:latest")
        self.skills = ["poetry", "verse", "lyricism", "metaphor", "rhyme"]

    async def _process(self, task, llm_client=None):
        return {"content": "Processed by Poet", "type": task.get("type", "generic")}
