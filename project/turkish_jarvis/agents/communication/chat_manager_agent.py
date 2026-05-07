from turkish_jarvis.agents.base_agent import BaseAgent


class ChatManagerAgent(BaseAgent):
    """Sohbet Yöneticisi — chat_management, messaging, conversation, threading."""

    def __init__(self):
        super().__init__("chatmanager", "Sohbet Yöneticisi", "Communication", "gemma4:latest")
        self.skills = ["chat_management", "messaging", "conversation", "threading"]

    async def _process(self, task, llm_client=None):
        return {"agent": "chatmanager", "processed": task.get("count", 0)}
