"""Ruflo Autopilot Plugin Bridge.

Otonom görev yürütme döngüsü: planla -> çalıştır -> gözlemle -> düzelt.
TypeScript'teki ``while (true) { observe(); plan(); act(); }`` yapısının
Python portu. Her iterasyon bir "cycle" olarak adlandırılır.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class CycleResult:
    """Bir otonom döngünün sonucu."""

    cycle_id: int
    status: str  # success / failed / stalled / aborted
    actions_taken: List[str] = field(default_factory=list)
    observations: List[str] = field(default_factory=list)
    corrections: List[str] = field(default_factory=list)
    elapsed_sec: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Bridge
# ---------------------------------------------------------------------------


class RufloAutopilot:
    """Autonomous execution loop inspired by ruflo-autopilot.

    Usage
    -----
    pilot = RufloAutopilot()
    pilot.set_strategy(my_strategy)
    results = await pilot.run(max_cycles=5)
    """

    def __init__(self, stall_threshold: int = 3) -> None:
        self.stall_threshold = stall_threshold
        self._strategy: Optional[Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = None
        self._history: List[CycleResult] = []
        self._state: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Strategy binding
    # ------------------------------------------------------------------

    def set_strategy(
        self,
        strategy: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],
    ) -> None:
        """Bind the strategy coroutine.

        A strategy receives the current ``state`` dict and must return
        a dict with at least keys ``action``, ``observation``.
        """
        self._strategy = strategy

    # ------------------------------------------------------------------
    # Core loop
    # ------------------------------------------------------------------

    async def run(
        self,
        max_cycles: int = 10,
        pause_sec: float = 0.5,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[CycleResult]:
        """Execute the autonomous loop.

        Parameters
        ----------
        max_cycles : int
            Maximum number of iterations.
        pause_sec : float
            Sleep between cycles.
        context : dict
            Initial state injected into the strategy.

        Returns
        -------
        List of ``CycleResult`` objects.
        """
        if self._strategy is None:
            raise RuntimeError("No strategy set. Call set_strategy() first.")

        self._state = dict(context or {})
        self._history.clear()
        stalled = 0

        for cycle_id in range(1, max_cycles + 1):
            t0 = time.time()
            try:
                response = await asyncio.wait_for(
                    self._strategy(self._state), timeout=30.0
                )
            except asyncio.TimeoutError:
                result = CycleResult(
                    cycle_id=cycle_id,
                    status="failed",
                    actions_taken=[],
                    observations=["Strategy timeout"],
                    corrections=[],
                    elapsed_sec=time.time() - t0,
                )
                self._history.append(result)
                break
            except Exception as exc:
                logger.exception("[ruflo-autopilot] cycle %d error", cycle_id)
                result = CycleResult(
                    cycle_id=cycle_id,
                    status="failed",
                    actions_taken=[],
                    observations=[str(exc)],
                    corrections=[],
                    elapsed_sec=time.time() - t0,
                )
                self._history.append(result)
                break

            action = response.get("action", "noop")
            observation = response.get("observation", "")
            correction = response.get("correction", "")
            done = response.get("done", False)

            # Update state
            self._state["last_action"] = action
            self._state["last_observation"] = observation
            self._state["cycle_id"] = cycle_id

            # Detect stall (same action repeated)
            if self._history and self._history[-1].actions_taken == [action]:
                stalled += 1
            else:
                stalled = 0

            status = "success"
            if stalled >= self.stall_threshold:
                status = "stalled"
            if done:
                status = "success"

            result = CycleResult(
                cycle_id=cycle_id,
                status=status,
                actions_taken=[action],
                observations=[observation],
                corrections=[correction] if correction else [],
                elapsed_sec=time.time() - t0,
                metadata=dict(response),
            )
            self._history.append(result)
            logger.info(
                "[ruflo-autopilot] cycle %d -> %s (%s)",
                cycle_id, action, status,
            )

            if done or status == "stalled":
                break

            if pause_sec:
                await asyncio.sleep(pause_sec)

        return self._history

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def get_history(self) -> List[CycleResult]:
        """Return the full cycle history."""
        return list(self._history)

    def get_state(self) -> Dict[str, Any]:
        """Return the current internal state."""
        return dict(self._state)

    def last_cycle(self) -> Optional[CycleResult]:
        """Return the most recent cycle result."""
        return self._history[-1] if self._history else None

    def summary(self) -> Dict[str, Any]:
        """High-level run statistics."""
        total = len(self._history)
        ok = sum(1 for r in self._history if r.status == "success")
        failed = sum(1 for r in self._history if r.status == "failed")
        stalled = sum(1 for r in self._history if r.status == "stalled")
        total_time = sum(r.elapsed_sec for r in self._history)
        return {
            "total_cycles": total,
            "success": ok,
            "failed": failed,
            "stalled": stalled,
            "total_time_sec": round(total_time, 2),
            "final_state": self._state,
        }

    # ------------------------------------------------------------------
    # Built-in demo strategy
    # ------------------------------------------------------------------

    @staticmethod
    async def demo_strategy(state: Dict[str, Any]) -> Dict[str, Any]:
        """A harmless demo strategy that counts down from 5."""
        count = state.get("count", 5)
        if count <= 0:
            return {"action": "finish", "observation": "Count reached zero", "done": True}
        return {
            "action": f"decrement({count})",
            "observation": f"Count was {count}",
            "correction": "",
            "done": False,
            "count": count - 1,
        }
