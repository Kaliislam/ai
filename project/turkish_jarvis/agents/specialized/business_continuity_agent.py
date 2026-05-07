"""BusinessContinuity Agent — İş sürekliliği."""

from turkish_jarvis.agents.base_agent import BaseAgent


class BusinessContinuityAgent(BaseAgent):
    """İş sürekliliği — BIA, RTO/RPO tanımlama, plan geliştirme."""

    def __init__(self):
        super().__init__("BusinessContinuity", "Business Continuity Manager", "Specialized", "qwen3-coder:30b")
        self.skills = ["bia", "rto_rpo", "bcp", "testing"]

    async def _process(self, task, llm_client=None):
        return {"continuity_plan": "updated", "action_taken": task.get("action")}
