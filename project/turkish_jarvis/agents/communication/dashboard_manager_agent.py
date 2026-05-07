from turkish_jarvis.agents.base_agent import BaseAgent


class DashboardManagerAgent(BaseAgent):
    """Dashboard Yöneticisi — dashboard_widgets, metrics, layout, real_time."""

    def __init__(self):
        super().__init__("dashboardmanager", "Dashboard Yöneticisi", "Communication", "gemma4:latest")
        self.skills = ["dashboard_widgets", "metrics", "layout", "real_time"]

    async def _process(self, task, llm_client=None):
        return {"agent": "dashboardmanager", "processed": task.get("count", 0)}
