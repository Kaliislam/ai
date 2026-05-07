from turkish_jarvis.agents.base_agent import BaseAgent


class VisualizationManagerAgent(BaseAgent):
    """Görselleştirme Yöneticisi — charts, graphs, plots, data_viz."""

    def __init__(self):
        super().__init__("visualizationmanager", "Görselleştirme Yöneticisi", "Communication", "gemma4:latest")
        self.skills = ["charts", "graphs", "plots", "data_viz"]

    async def _process(self, task, llm_client=None):
        return {"agent": "visualizationmanager", "processed": task.get("count", 0)}
