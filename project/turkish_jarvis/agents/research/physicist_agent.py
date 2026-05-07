from turkish_jarvis.agents.base_agent import BaseAgent


class PhysicistAgent(BaseAgent):
    """Fizikci ajani — fiziksel sistem analizi ve simulasyon."""
    def __init__(self):
        super().__init__("Physicist", "Physicist", "Research", "qwen3-coder:30b")
        self.skills = ["mechanics", "thermodynamics", "electromagnetism", "simulation"]

    async def _process(self, task, llm_client=None):
        # Fiziksel analiz mantigi
        system = task.get('system', '')
        return {'simulation': 'run', 'system': system, 'parameters': {}}
