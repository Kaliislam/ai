"""Ruflo Swarm Plugin Bridge.

Lightweight multi-agent orchestration inspired by ruflo-swarm.
No external dependencies beyond stdlib + asyncio.
Provides: agent registry, task broadcast, result aggregation,
and a simple round-robin / priority dispatcher.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class AgentSpec:
    """Descriptor for a swarm agent."""

    agent_id: str
    name: str
    role: str  # e.g. "researcher", "coder", "reviewer"
    priority: int = 5  # lower = higher priority
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SwarmTask:
    """Task routed through the swarm."""

    task_id: str
    task_type: str
    payload: Dict[str, Any]
    assigned_to: Optional[str] = None
    status: str = "pending"  # pending / running / done / failed
    result: Any = None
    created_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None


# ---------------------------------------------------------------------------
# Bridge
# ---------------------------------------------------------------------------


class RufloSwarm:
    """Minimal swarm orchestrator.

    Usage
    -----
    swarm = RufloSwarm()
    swarm.register_agent(AgentSpec("a1", "Coder", "coder"))
    task = swarm.submit_task("code_review", {"file": "foo.py"})
    results = await swarm.dispatch_all()
    """

    def __init__(self, max_concurrency: int = 4) -> None:
        self.agents: Dict[str, AgentSpec] = {}
        self.tasks: List[SwarmTask] = []
        self.handlers: Dict[str, Callable[[SwarmTask], Awaitable[Any]]] = {}
        self.max_concurrency = max_concurrency
        self._results: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Agent registry
    # ------------------------------------------------------------------

    def register_agent(self, spec: AgentSpec) -> None:
        """Add an agent to the swarm."""
        self.agents[spec.agent_id] = spec
        logger.info("[ruflo-swarm] registered agent %s (%s)", spec.agent_id, spec.role)

    def unregister_agent(self, agent_id: str) -> bool:
        """Remove an agent."""
        return self.agents.pop(agent_id, None) is not None

    def list_agents(self, role: Optional[str] = None) -> List[AgentSpec]:
        """List agents, optionally filtered by role."""
        specs = list(self.agents.values())
        if role:
            specs = [s for s in specs if s.role == role]
        return sorted(specs, key=lambda s: s.priority)

    # ------------------------------------------------------------------
    # Task lifecycle
    # ------------------------------------------------------------------

    def submit_task(self, task_type: str, payload: Dict[str, Any]) -> SwarmTask:
        """Enqueue a new task."""
        task = SwarmTask(
            task_id=f"task_{uuid.uuid4().hex[:8]}",
            task_type=task_type,
            payload=payload,
        )
        self.tasks.append(task)
        logger.debug("[ruflo-swarm] submitted %s (%s)", task.task_id, task_type)
        return task

    def register_handler(self, task_type: str, handler: Callable[[SwarmTask], Awaitable[Any]]) -> None:
        """Bind a handler coroutine to a task type."""
        self.handlers[task_type] = handler
        logger.debug("[ruflo-swarm] handler registered for %s", task_type)

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    async def dispatch_all(self, timeout: float = 60.0) -> Dict[str, Any]:
        """Run all pending tasks concurrently (up to max_concurrency).

        Returns a mapping ``task_id -> result | error``.
        """
        pending = [t for t in self.tasks if t.status == "pending"]
        if not pending:
            return {}

        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def _run_one(task: SwarmTask) -> None:
            handler = self.handlers.get(task.task_type)
            if handler is None:
                task.status = "failed"
                task.result = f"No handler for task type '{task.task_type}'"
                return
            async with semaphore:
                task.status = "running"
                task.assigned_to = self._pick_agent(task.task_type)
                try:
                    task.result = await asyncio.wait_for(
                        handler(task), timeout=timeout
                    )
                    task.status = "done"
                except asyncio.TimeoutError:
                    task.status = "failed"
                    task.result = "timeout"
                except Exception as exc:
                    task.status = "failed"
                    task.result = f"{type(exc).__name__}: {exc}"
                task.finished_at = time.time()

        await asyncio.gather(*(_run_one(t) for t in pending))
        self._results = {t.task_id: t.result for t in self.tasks}
        return self._results

    def _pick_agent(self, task_type: str) -> Optional[str]:
        """Simple round-robin-ish agent selection by capability overlap."""
        candidates = [
            a for a in self.agents.values()
            if task_type in a.capabilities or not a.capabilities
        ]
        if not candidates:
            candidates = list(self.agents.values())
        best = min(candidates, key=lambda a: a.priority)
        return best.agent_id if best else None

    # ------------------------------------------------------------------
    # Results & reporting
    # ------------------------------------------------------------------

    def get_results(self) -> Dict[str, Any]:
        """Return the latest task results."""
        return self._results.copy()

    def get_task(self, task_id: str) -> Optional[SwarmTask]:
        """Lookup a task by ID."""
        for t in self.tasks:
            if t.task_id == task_id:
                return t
        return None

    def summary(self) -> Dict[str, Any]:
        """Swarm health / workload summary."""
        by_status: Dict[str, int] = {}
        for t in self.tasks:
            by_status[t.status] = by_status.get(t.status, 0) + 1
        return {
            "agents_registered": len(self.agents),
            "total_tasks": len(self.tasks),
            "status_breakdown": by_status,
            "handlers_registered": list(self.handlers.keys()),
        }

    def reset(self) -> None:
        """Clear tasks and results (keep agents / handlers)."""
        self.tasks.clear()
        self._results.clear()

    # ------------------------------------------------------------------
    # Convenience: built-in mock handlers for common types
    # ------------------------------------------------------------------

    def enable_mock_handlers(self) -> None:
        """Register trivial echo handlers so the swarm is testable standalone."""

        async def echo_handler(task: SwarmTask) -> Dict[str, Any]:
            await asyncio.sleep(0.05)
            return {"echo": task.payload, "agent": task.assigned_to}

        for task_type in ("research", "code", "review", "summarize", "test"):
            self.register_handler(task_type, echo_handler)
