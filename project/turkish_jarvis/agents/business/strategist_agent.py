"""Strategist Agent — iş stratejisi ve planlama."""

from turkish_jarvis.agents.base_agent import BaseAgent

class StrategistAgent(BaseAgent):
    """Stratejist ajanı — iş stratejisi ve planlama."""
    def __init__(self):
        super().__init__("Strategist", "Strategist", "Business", "gemma4:latest")
        self.skills = ["strategy", "business planning", "competitive analysis", "roadmapping", "kpis"]

    async def _process(self, task, llm_client=None):
        return {"content": "Processed by Strategist", "type": task.get("type", "generic")}
