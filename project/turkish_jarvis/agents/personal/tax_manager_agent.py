from turkish_jarvis.agents.base_agent import BaseAgent


class TaxManagerAgent(BaseAgent):
    """Vergi Yöneticisi — tax_calculation, filing, deductions, compliance."""

    def __init__(self):
        super().__init__("taxmanager", "Vergi Yöneticisi", "Personal", "gemma4:latest")
        self.skills = ["tax_calculation", "filing", "deductions", "compliance"]

    async def _process(self, task, llm_client=None):
        return {"agent": "taxmanager", "processed": task.get("count", 0)}
