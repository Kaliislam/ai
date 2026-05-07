from turkish_jarvis.agents.base_agent import BaseAgent


class APIEngineer(BaseAgent):
    """API geliştirici -- REST, GraphQL ve gRPC servis tasarimi."""

    def __init__(self):
        super().__init__("APIDev", "API Engineer", "Engineering")
        self.skills = ["rest", "graphql", "grpc", "openapi", "rate_limiting"]

    async def _process(self, task, llm_client=None):
        return {"action": "api_design", "protocol": task.get("protocol")}
