from turkish_jarvis.agents.base_agent import BaseAgent


class ChiefOperatingOfficer(BaseAgent):
    """Operasyon şefi -- iş süreçleri ve verimlilik optimizasyonu."""

    def __init__(self):
        super().__init__("COO", "Chief Operating Officer", "Executive", "llama3.1:70b")
        self.skills = ["operations", "workflow", "efficiency", "process_design"]

    async def _process(self, task, llm_client=None):
        return {"action": "ops_optimization", "process": task.get("workflow")}
