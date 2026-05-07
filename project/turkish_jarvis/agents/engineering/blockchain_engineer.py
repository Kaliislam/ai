from turkish_jarvis.agents.base_agent import BaseAgent


class BlockchainEngineer(BaseAgent):
    """Blockchain geliştirici -- akilli kontratlar ve DApp'ler."""

    def __init__(self):
        super().__init__("BlockchainDev", "Blockchain Engineer", "Engineering")
        self.skills = ["solidity", "ethersjs", "web3", "defi", "smart_contracts"]

    async def _process(self, task, llm_client=None):
        return {"action": "smart_contract", "chain": task.get("chain")}
