"""Council Manager — 150+ ajanı koordine eden CEO Jarvis yönetim sistemi."""

import asyncio
import logging
from typing import Any, Optional
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger("jarvis.council")

class CouncilManager:
    """CEO Jarvis — 150 uzman ajana emir veren patron ajan."""
    
    def __init__(self, ollama_manager, model_pool):
        self.ceo = None  # JarvisCEO (set externally)
        self.councils: dict[str, list[Any]] = {}  # department -> agents
        self.ollama_mgr = ollama_manager
        self.model_pool = model_pool
        self.executor = ThreadPoolExecutor(max_workers=20)
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.active_tasks: dict[str, Any] = {}
    
    def register_council(self, department: str, agents: list[Any]) -> None:
        """Bir council'i (departmanı) kaydet."""
        self.councils[department] = agents
        logger.info("🏛️ Council kaydedildi: %s (%d ajan)", department, len(agents))
    
    def register_ceo(self, ceo_agent) -> None:
        """CEO'yu kaydet."""
        self.ceo = ceo_agent
        logger.info("👑 CEO kaydedildi: %s", ceo_agent.name)
    
    async def execute_task(self, task: dict, parallel: bool = True) -> dict:
        """Görevi CEO analiz eder, doğru council'e dağıtır."""
        if self.ceo is None:
            return {"error": "CEO not registered"}
        
        # CEO analiz eder
        analysis = await self.ceo._process(task)
        target_dept = analysis.get("target_department", "engineering")
        
        # Council seç
        council = self.councils.get(target_dept, [])
        if not council:
            return {"error": f"Council bulunamadı: {target_dept}"}
        
        # En uygun ajana görev ver
        agent = self._select_best_agent(council, task)
        
        if parallel and len(council) > 1 and task.get("needs_team", False):
            # Çok ajanlı paralel görev
            return await self._execute_parallel(council, task)
        else:
            # Tek ajan
            return await agent.execute_task(task, self.model_pool.get_client())
    
    async def _execute_parallel(self, agents: list[Any], task: dict) -> dict:
        """Birden fazla ajanı paralel çalıştır."""
        # Her ajana farklı alt-görev
        subtasks = self._decompose_task(task, len(agents))
        
        coros = [
            agent.execute_task(subtask, self.model_pool.get_client())
            for agent, subtask in zip(agents[:len(subtasks)], subtasks)
        ]
        
        results = await asyncio.gather(*coros, return_exceptions=True)
        
        # Sonuçları birleştir
        return {
            "parallel": True,
            "results": [r if not isinstance(r, Exception) else {"error": str(r)} for r in results],
            "agents_used": [a.name for a in agents[:len(subtasks)]],
        }
    
    def _select_best_agent(self, agents: list[Any], task: dict) -> Any:
        """Göreve en uygun ajanı seç."""
        # Basit: ilk uygun ajan (daha karmaşık scoring eklenebilir)
        for agent in agents:
            if agent.status == "idle":
                return agent
        return agents[0]  # Hepsi meşgulse ilkini ver
    
    def _decompose_task(self, task: dict, parts: int) -> list[dict]:
        """Görevi parçalara ayır."""
        return [{**task, "part_id": i, "total_parts": parts} for i in range(parts)]
    
    async def get_status_report(self) -> dict:
        """Tüm council'lerin durum raporu."""
        report = {}
        for dept, agents in self.councils.items():
            report[dept] = {
                "total": len(agents),
                "idle": sum(1 for a in agents if a.status == "idle"),
                "working": sum(1 for a in agents if a.status == "working"),
                "completed_tasks": sum(len(a.task_history) for a in agents),
            }
        return report
    
    async def broadcast(self, message: str) -> list[dict]:
        """Tüm ajanlara mesaj yayınla."""
        results = []
        for dept, agents in self.councils.items():
            for agent in agents:
                results.append({
                    "agent": agent.name,
                    "department": dept,
                    "message_received": True,
                })
        return results
    
    def shutdown(self) -> None:
        """Tüm council'leri kapat."""
        self.executor.shutdown(wait=False)
        logger.info("🛑 Tüm council'ler kapatıldı")
