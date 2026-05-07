from turkish_jarvis.agents.base_agent import BaseAgent


class NetworkEngineer(BaseAgent):
    """Ağ mühendisi -- topoloji, güvenlik duvarlari ve yük dengeleme."""

    def __init__(self):
        super().__init__("NetEng", "Network Engineer", "Engineering")
        self.skills = ["tcp_ip", "vpn", "load_balancing", "firewalls", "cdn"]

    async def _process(self, task, llm_client=None):
        return {"action": "network_setup", "topology": task.get("topology")}
