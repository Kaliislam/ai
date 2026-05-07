from turkish_jarvis.agents.base_agent import BaseAgent


class PolicyExpertAgent(BaseAgent):
    """Politika Uzmanı — policy_analysis, legislation, governance, advocacy."""

    def __init__(self):
        super().__init__("policyexpert", "Politika Uzmanı", "Knowledge", "gemma4:latest")
        self.skills = ["policy_analysis", "legislation", "governance", "advocacy"]

    async def _process(self, task, llm_client=None):
        return {"agent": "policyexpert", "processed": task.get("count", 0)}
