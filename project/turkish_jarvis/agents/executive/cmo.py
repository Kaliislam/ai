from turkish_jarvis.agents.base_agent import BaseAgent


class ChiefMarketingOfficer(BaseAgent):
    """Pazarlama şefi -- marka stratejisi, büyüme ve kullanici edinimi."""

    def __init__(self):
        super().__init__("CMO", "Chief Marketing Officer", "Executive", "llama3.1:70b")
        self.skills = ["branding", "growth", "seo", "analytics", "social_media"]

    async def _process(self, task, llm_client=None):
        return {"action": "marketing_campaign", "channel": task.get("channel")}
