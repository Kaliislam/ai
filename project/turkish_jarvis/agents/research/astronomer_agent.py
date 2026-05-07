from turkish_jarvis.agents.base_agent import BaseAgent


class AstronomerAgent(BaseAgent):
    """Astronom ajani — gokcismi analizi ve hesaplama."""
    def __init__(self):
        super().__init__("Astronomer", "Astronomer", "Research", "qwen3-coder:30b")
        self.skills = ["celestial_mechanics", "observation_planning", "data_reduction", "cataloging"]

    async def _process(self, task, llm_client=None):
        # Astronomik analiz mantigi
        object_id = task.get('object', '')
        return {'observation': 'analyzed', 'object': object_id, 'coordinates': {}}
