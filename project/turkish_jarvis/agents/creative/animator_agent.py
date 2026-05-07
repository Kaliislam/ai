"""Animator Agent — 2D/3D animasyon üretimi."""

from turkish_jarvis.agents.base_agent import BaseAgent

class AnimatorAgent(BaseAgent):
    """Animatör ajanı — 2D/3D animasyon üretimi."""
    def __init__(self):
        super().__init__("Animator", "Animator", "Creative", "gemma4:latest")
        self.skills = ["2d animation", "3d animation", "motion graphics", "character animation", "storyboarding"]

    async def _process(self, task, llm_client=None):
        return {"content": "Processed by Animator", "type": task.get("type", "generic")}
