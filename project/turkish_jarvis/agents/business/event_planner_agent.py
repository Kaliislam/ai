"""EventPlanner Agent — etkinlik organizasyonu."""

from turkish_jarvis.agents.base_agent import BaseAgent

class EventPlannerAgent(BaseAgent):
    """Etkinlik planlayıcı ajanı — etkinlik organizasyonu."""
    def __init__(self):
        super().__init__("EventPlanner", "Event Planner", "Business", "gemma4:latest")
        self.skills = ["event planning", "logistics", "vendor management", "scheduling", "coordination"]

    async def _process(self, task, llm_client=None):
        return {"content": "Processed by EventPlanner", "type": task.get("type", "generic")}
