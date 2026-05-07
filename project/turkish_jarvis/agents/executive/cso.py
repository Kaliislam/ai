from turkish_jarvis.agents.base_agent import BaseAgent


class ChiefSecurityOfficer(BaseAgent):
    """Güvenlik şefi -- siber güvenlik, risk yönetimi ve uyumluluk."""

    def __init__(self):
        super().__init__("CSO", "Chief Security Officer", "Executive", "llama3.1:70b")
        self.skills = ["cybersecurity", "risk_assessment", "compliance", "incident_response"]

    async def _process(self, task, llm_client=None):
        return {"action": "security_audit", "threat_level": task.get("severity", "low")}
