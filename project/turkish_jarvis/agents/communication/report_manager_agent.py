from turkish_jarvis.agents.base_agent import BaseAgent


class ReportManagerAgent(BaseAgent):
    """Rapor Yöneticisi — report_generation, templates, data_export, scheduling."""

    def __init__(self):
        super().__init__("reportmanager", "Rapor Yöneticisi", "Communication", "gemma4:latest")
        self.skills = ["report_generation", "templates", "data_export", "scheduling"]

    async def _process(self, task, llm_client=None):
        return {"agent": "reportmanager", "processed": task.get("count", 0)}
