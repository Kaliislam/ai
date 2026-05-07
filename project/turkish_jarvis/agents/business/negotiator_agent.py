"""Negotiator Agent — anlaşma ve müzakere stratejisi."""

from turkish_jarvis.agents.base_agent import BaseAgent

class NegotiatorAgent(BaseAgent):
    """Müzakereci ajanı — anlaşma ve müzakere stratejisi."""
    def __init__(self):
        super().__init__("Negotiator", "Negotiator", "Business", "gemma4:latest")
        self.skills = ["negotiation", "deal making", "contract terms", "conflict resolution", "persuasion"]

    async def _process(self, task, llm_client=None):
        return {"content": "Processed by Negotiator", "type": task.get("type", "generic")}
