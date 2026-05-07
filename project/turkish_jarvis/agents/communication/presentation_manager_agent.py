from turkish_jarvis.agents.base_agent import BaseAgent


class PresentationManagerAgent(BaseAgent):
    """Sunum Yöneticisi — slides, templates, design, export."""

    def __init__(self):
        super().__init__("presentationmanager", "Sunum Yöneticisi", "Communication", "gemma4:latest")
        self.skills = ["slides", "templates", "design", "export"]

    async def _process(self, task, llm_client=None):
        return {"agent": "presentationmanager", "processed": task.get("count", 0)}
