from turkish_jarvis.agents.base_agent import BaseAgent


class CloudEngineer(BaseAgent):
    """Bulut mühendisi -- AWS, GCP, Azure altyapi yönetimi."""

    def __init__(self):
        super().__init__("CloudEng", "Cloud Engineer", "Engineering")
        self.skills = ["aws", "gcp", "azure", "serverless", "cost_optimization"]

    async def _process(self, task, llm_client=None):
        return {"action": "cloud_infra", "provider": task.get("provider")}
