from turkish_jarvis.agents.base_agent import BaseAgent


class UIDesignerAgent(BaseAgent):
    """UI tasarimci ajani — arayuz tasarimi ve stil rehberi."""
    def __init__(self):
        super().__init__("UIDesigner", "UI Designer", "Operations", "qwen3-coder:30b")
        self.skills = ["interface_design", "design_systems", "prototyping", "visual_composition"]

    async def _process(self, task, llm_client=None):
        # Arayuz tasarimi mantigi
        screens = task.get('screens', [])
        return {'design': 'created', 'screens': screens, 'style_guide': {}}
