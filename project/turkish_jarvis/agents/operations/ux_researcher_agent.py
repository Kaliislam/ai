from turkish_jarvis.agents.base_agent import BaseAgent


class UXResearcherAgent(BaseAgent):
    """UX arastirmaci ajani — kullanici arastirmasi ve test."""
    def __init__(self):
        super().__init__("UXResearcher", "UX Researcher", "Operations", "qwen3-coder:30b")
        self.skills = ["user_interviews", "usability_testing", "persona_creation", "journey_mapping"]

    async def _process(self, task, llm_client=None):
        # Kullanici arastirmasi mantigi
        users = task.get('users', [])
        return {'research': 'done', 'insights': [], 'participants': len(users)}
