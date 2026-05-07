"""IncidentResponder Agent — Olay müdahale."""

from turkish_jarvis.agents.base_agent import BaseAgent


class IncidentResponderAgent(BaseAgent):
    """Olay müdahale — containment, eradikasyon, lessons learned."""

    def __init__(self):
        super().__init__("IncidentResponder", "Incident Responder", "Specialized", "qwen3-coder:30b")
        self.skills = ["containment", "eradication", "recovery", "lessons"]

    async def _process(self, task, llm_client=None):
        return {"incident_status": "contained", "action_taken": task.get("action")}
