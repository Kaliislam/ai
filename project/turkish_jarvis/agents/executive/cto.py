from turkish_jarvis.agents.base_agent import BaseAgent


class ChiefTechnologyOfficer(BaseAgent):
    """Teknoloji şefi -- yazılım mimarisi ve teknoloji yıgını kararlari."""

    def __init__(self):
        super().__init__("CTO", "Chief Technology Officer", "Executive", "llama3.1:70b")
        self.skills = ["architecture", "tech_stack", "scalability", "roadmap"]

    async def _process(self, task, llm_client=None):
        return {"action": "tech_review", "decision": task.get("technology")}
