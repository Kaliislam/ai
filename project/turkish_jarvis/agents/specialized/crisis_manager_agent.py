"""CrisisManager Agent — Kriz yöneticisi."""

from turkish_jarvis.agents.base_agent import BaseAgent


class CrisisManagerAgent(BaseAgent):
    """Kriz yöneticisi — kriz komuta merkezi, iletişim, koordinasyon."""

    def __init__(self):
        super().__init__("CrisisManager", "Crisis Manager", "Specialized", "qwen3-coder:30b")
        self.skills = ["command_center", "communication", "coordination", "escalation"]

    async def _process(self, task, llm_client=None):
        return {"crisis_status": "managed", "action_taken": task.get("action")}
