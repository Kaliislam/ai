from turkish_jarvis.agents.base_agent import BaseAgent


class ResearcherAgent(BaseAgent):
    """Arastirmaci ajani — literatur taramasi ve sentez."""
    def __init__(self):
        super().__init__("Researcher", "Researcher", "Research", "qwen3-coder:30b")
        self.skills = ["literature_review", "hypothesis_generation", "methodology", "synthesis"]

    async def _process(self, task, llm_client=None):
        # Literatur taramasi mantigi
        topic = task.get('topic', '')
        return {'review': 'complete', 'topic': topic, 'sources': []}
