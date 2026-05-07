from turkish_jarvis.agents.base_agent import BaseAgent


class InsuranceManagerAgent(BaseAgent):
    """Sigorta Yöneticisi — policy_tracking, claims, coverage, renewals."""

    def __init__(self):
        super().__init__("insurancemanager", "Sigorta Yöneticisi", "Personal", "gemma4:latest")
        self.skills = ["policy_tracking", "claims", "coverage", "renewals"]

    async def _process(self, task, llm_client=None):
        return {"agent": "insurancemanager", "processed": task.get("count", 0)}
