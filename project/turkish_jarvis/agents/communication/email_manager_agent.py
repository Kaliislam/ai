from turkish_jarvis.agents.base_agent import BaseAgent


class EmailManagerAgent(BaseAgent):
    """E-posta Yöneticisi — email_management, filtering, scheduling, drafting."""

    def __init__(self):
        super().__init__("emailmanager", "E-posta Yöneticisi", "Communication", "gemma4:latest")
        self.skills = ["email_management", "filtering", "scheduling", "drafting"]

    async def _process(self, task, llm_client=None):
        return {"agent": "emailmanager", "processed": task.get("count", 0)}
