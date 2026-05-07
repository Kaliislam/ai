"""Ruflo Loop Workers Plugin Bridge.

Periyodik worker / task scheduler. asyncio tabanlı.
Jobs register edilir, belirtilen interval ile çalışır.
Graceful shutdown, retry policy, ve backpressure desteği vardır.
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
class JobSpec:
    """Bir periyodik job'un tanımı."""

    job_id: str
    name: str
    interval_sec: float
    handler: Callable[[], Awaitable[Any]]
    max_retries: int = 3
    retry_delay_sec: float = 1.0
    enabled: bool = True
    tags: List[str] = field(default_factory=list)


@dataclass
class JobRun:
    """Tek bir çalıştırma kaydı."""

    job_id: str
    start: float
    end: Optional[float] = None
    success: bool = False
    error: Optional[str] = None
    attempt: int = 1


# ---------------------------------------------------------------------------
# Bridge
# ---------------------------------------------------------------------------


class RufloLoopWorkers:
    """Periodic worker scheduler inspired by ruflo-loop-workers.

    Usage
    -----
    workers = RufloLoopWorkers()
    workers.add_job("heartbeat", 30.0, heartbeat_fn)
    await workers.start()
    ...
    await workers.stop()
    """

    def __init__(self) -> None:
        self.jobs: Dict[str, JobSpec] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        self._runs: List[JobRun] = []
        self._running = False
        self._shutdown_event: Optional[asyncio.Event] = None

    # ------------------------------------------------------------------
    # Job registry
    # ------------------------------------------------------------------

    def add_job(
        self,
        job_id: str,
        interval_sec: float,
        handler: Callable[[], Awaitable[Any]],
        name: Optional[str] = None,
        max_retries: int = 3,
        retry_delay_sec: float = 1.0,
        tags: Optional[List[str]] = None,
    ) -> JobSpec:
        """Register a periodic job."""
        spec = JobSpec(
            job_id=job_id,
            name=name or job_id,
            interval_sec=interval_sec,
            handler=handler,
            max_retries=max_retries,
            retry_delay_sec=retry_delay_sec,
            tags=tags or [],
        )
        self.jobs[job_id] = spec
        logger.info("[ruflo-loop-workers] registered %s (%ds)", job_id, interval_sec)
        return spec

    def remove_job(self, job_id: str) -> bool:
        """Remove a job and cancel its running task."""
        spec = self.jobs.pop(job_id, None)
        if spec is None:
            return False
        task = self._tasks.pop(job_id, None)
        if task and not task.done():
            task.cancel()
        return True

    def list_jobs(self) -> List[JobSpec]:
        return list(self.jobs.values())

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start all registered jobs."""
        if self._running:
            return
        self._running = True
        self._shutdown_event = asyncio.Event()
        for job_id, spec in self.jobs.items():
            if spec.enabled:
                self._tasks[job_id] = asyncio.create_task(
                    self._loop_job(spec), name=f"job_{job_id}"
                )
        logger.info("[ruflo-loop-workers] started %d jobs", len(self._tasks))

    async def stop(self, timeout: float = 5.0) -> None:
        """Graceful shutdown: cancel tasks, wait for timeout."""
        if not self._running:
            return
        self._running = False
        if self._shutdown_event:
            self._shutdown_event.set()

        # Cancel all
        for task in self._tasks.values():
            if not task.done():
                task.cancel()

        # Wait
        pending = [t for t in self._tasks.values() if not t.done()]
        if pending:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*pending, return_exceptions=True),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                logger.warning("[ruflo-loop-workers] shutdown timeout")
        self._tasks.clear()
        logger.info("[ruflo-loop-workers] stopped")

    # ------------------------------------------------------------------
    # Internal loop
    # ------------------------------------------------------------------

    async def _loop_job(self, spec: JobSpec) -> None:
        while self._running and (self._shutdown_event is None or not self._shutdown_event.is_set()):
            t0 = time.time()
            run = JobRun(job_id=spec.job_id, start=t0)
            success = False
            for attempt in range(1, spec.max_retries + 1):
                try:
                    await asyncio.wait_for(spec.handler(), timeout=spec.interval_sec * 2)
                    success = True
                    break
                except asyncio.TimeoutError:
                    run.error = "handler_timeout"
                except Exception as exc:
                    run.error = f"{type(exc).__name__}: {exc}"
                    logger.warning(
                        "[ruflo-loop-workers] %s attempt %d failed: %s",
                        spec.job_id, attempt, run.error,
                    )
                run.attempt = attempt
                if attempt < spec.max_retries:
                    await asyncio.sleep(spec.retry_delay_sec)

            run.success = success
            run.end = time.time()
            self._runs.append(run)

            if not self._running:
                break

            # Backpressure: if execution took longer than interval, skip sleep
            elapsed = time.time() - t0
            sleep_for = spec.interval_sec - elapsed
            if sleep_for > 0:
                try:
                    await asyncio.wait_for(
                        self._shutdown_event.wait() if self._shutdown_event else asyncio.sleep(sleep_for),
                        timeout=sleep_for,
                    )
                except asyncio.TimeoutError:
                    pass

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_runs(self, job_id: Optional[str] = None, limit: int = 100) -> List[JobRun]:
        runs = self._runs
        if job_id:
            runs = [r for r in runs if r.job_id == job_id]
        return runs[-limit:]

    def summary(self) -> Dict[str, Any]:
        by_job: Dict[str, Dict[str, Any]] = {}
        for spec in self.jobs.values():
            runs = [r for r in self._runs if r.job_id == spec.job_id]
            ok = sum(1 for r in runs if r.success)
            fail = len(runs) - ok
            by_job[spec.job_id] = {
                "name": spec.name,
                "interval_sec": spec.interval_sec,
                "total_runs": len(runs),
                "success": ok,
                "failed": fail,
                "enabled": spec.enabled,
            }
        return {
            "running": self._running,
            "jobs_registered": len(self.jobs),
            "jobs_active": len(self._tasks),
            "job_stats": by_job,
        }

    # ------------------------------------------------------------------
    # One-shot helper
    # ------------------------------------------------------------------

    async def run_once(self, job_id: str) -> Optional[JobRun]:
        """Manually trigger a single run of a registered job."""
        spec = self.jobs.get(job_id)
        if spec is None:
            return None
        t0 = time.time()
        run = JobRun(job_id=job_id, start=t0)
        try:
            await spec.handler()
            run.success = True
        except Exception as exc:
            run.error = str(exc)
        run.end = time.time()
        self._runs.append(run)
        return run
