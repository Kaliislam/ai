"""StorageAdmin Agent — Depolama yöneticisi."""

from turkish_jarvis.agents.base_agent import BaseAgent


class StorageAdminAgent(BaseAgent):
    """Depolama yöneticisi — disk, SAN, NAS yönetimi."""

    def __init__(self):
        super().__init__("StorageAdmin", "Storage Administrator", "Systems", "qwen3-coder:30b")
        self.skills = ["san", "nas", "disk_management", "tiering"]

    async def _process(self, task, llm_client=None):
        return {"storage_status": "checked", "action_taken": task.get("action")}
