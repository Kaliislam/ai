"""EthicalHacker Agent — Etik hacker."""

from turkish_jarvis.agents.base_agent import BaseAgent


class EthicalHackerAgent(BaseAgent):
    """Etik hacker — yetkili penetrasyon, güvenlik değerlendirmesi."""

    def __init__(self):
        super().__init__("EthicalHacker", "Ethical Hacker", "Specialized", "qwen3-coder:30b")
        self.skills = ["pentest", "exploit", "social_eng", "red_team"]

    async def _process(self, task, llm_client=None):
        return {"ethical_hack": "executed", "action_taken": task.get("action")}
