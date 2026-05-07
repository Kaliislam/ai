"""SysAdmin Agent — Sistem yöneticisi."""

from turkish_jarvis.agents.base_agent import BaseAgent


class SysAdminAgent(BaseAgent):
    """Sistem yöneticisi — sunucu, sistem, kaynak yönetimi."""

    def __init__(self):
        super().__init__("SysAdmin", "System Administrator", "Systems", "qwen3-coder:30b")
        self.skills = ["server_management", "monitoring", "troubleshooting", "automation"]

    async def _process(self, task, llm_client=None):
        return {"system_status": "checked", "action_taken": task.get("action")}
