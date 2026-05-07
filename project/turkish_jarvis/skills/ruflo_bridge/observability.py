"""Ruflo Observability Plugin Bridge.

Metrics, logging, tracing — stdlib-only, zero external deps.
Wraps Python logging and adds: structured JSON lines, simple
metric counters, timing spans, and health-check aggregation.
"""

from __future__ import annotations

import json
import logging
import sys
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class MetricPoint:
    """Single metric observation."""

    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class TraceSpan:
    """Simple trace span."""

    span_id: str
    name: str
    start: float
    end: Optional[float] = None
    parent_id: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        end = self.end or time.time()
        return round((end - self.start) * 1000, 2)


# ---------------------------------------------------------------------------
# Bridge
# ---------------------------------------------------------------------------


class RufloObservability:
    """Lightweight observability layer inspired by ruflo-observability.

    Usage
    -----
    obs = RufloObservability()
    obs.increment("api_calls")
    with obs.span("db_query"):
        run_query()
    obs.health_check("db", db_ping)
    snap = obs.snapshot()
    """

    def __init__(self, service_name: str = "turkish_jarvis") -> None:
        self.service_name = service_name
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._spans: List[TraceSpan] = []
        self._checks: Dict[str, bool] = {}
        self._check_funcs: Dict[str, Callable[[], bool]] = {}
        self._start_time = time.time()

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def increment(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        self._counters[name] = self._counters.get(name, 0) + value
        logger.debug("[ruflo-observability] counter %s += %d", name, value)

    def gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge value."""
        self._gauges[name] = value

    def get_counter(self, name: str) -> int:
        return self._counters.get(name, 0)

    def get_gauge(self, name: str) -> float:
        return self._gauges.get(name, 0.0)

    # ------------------------------------------------------------------
    # Timing / tracing
    # ------------------------------------------------------------------

    def span(self, name: str, parent_id: Optional[str] = None, tags: Optional[Dict[str, str]] = None) -> "_SpanContext":
        """Return a context manager that measures a span."""
        span_id = f"span_{int(time.time()*1000)}_{name}"
        span = TraceSpan(
            span_id=span_id,
            name=name,
            start=time.time(),
            parent_id=parent_id,
            tags=tags or {},
        )
        self._spans.append(span)
        return _SpanContext(span, self)

    def timeit(self, name: str) -> Callable[[Callable[[], T]], Callable[[], T]]:
        """Decorator that times a function and stores the span."""
        def decorator(fn: Callable[[], T]) -> Callable[[], T]:
            def wrapper() -> T:
                with self.span(name):
                    return fn()
            return wrapper
        return decorator

    def get_spans(self, name: Optional[str] = None) -> List[TraceSpan]:
        spans = self._spans
        if name:
            spans = [s for s in spans if s.name == name]
        return spans

    # ------------------------------------------------------------------
    # Health checks
    # ------------------------------------------------------------------

    def register_health_check(self, name: str, check_fn: Callable[[], bool]) -> None:
        """Register a zero-arg boolean health check."""
        self._check_funcs[name] = check_fn

    def run_health_checks(self) -> Dict[str, bool]:
        """Execute all registered checks and return results."""
        results: Dict[str, bool] = {}
        for name, fn in self._check_funcs.items():
            try:
                results[name] = bool(fn())
            except Exception:
                results[name] = False
        self._checks = results
        return results

    # ------------------------------------------------------------------
    # Snapshot / export
    # ------------------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        """Full observability snapshot."""
        uptime = round(time.time() - self._start_time, 2)
        checks = self.run_health_checks()
        return {
            "service": self.service_name,
            "uptime_sec": uptime,
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "health": checks,
            "spans": [
                {
                    "span_id": s.span_id,
                    "name": s.name,
                    "duration_ms": s.duration_ms,
                    "parent_id": s.parent_id,
                    "tags": s.tags,
                }
                for s in self._spans[-50:]
            ],
        }

    def snapshot_json(self) -> str:
        """Snapshot as a single JSON line."""
        return json.dumps(self.snapshot(), ensure_ascii=False)

    def log_structured(self, level: str, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Emit a structured JSON log line."""
        record = {
            "ts": time.time(),
            "svc": self.service_name,
            "lvl": level,
            "msg": message,
        }
        if extra:
            record.update(extra)
        print(json.dumps(record, ensure_ascii=False), file=sys.stderr)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Clear all mutable state (counters, spans, etc.)."""
        self._counters.clear()
        self._gauges.clear()
        self._spans.clear()
        self._checks.clear()
        self._start_time = time.time()


# ---------------------------------------------------------------------------
# Internal span context manager
# ---------------------------------------------------------------------------


class _SpanContext:
    def __init__(self, span: TraceSpan, obs: RufloObservability) -> None:
        self.span = span
        self.obs = obs

    def __enter__(self) -> TraceSpan:
        return self.span

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.span.end = time.time()
        if exc_val:
            self.span.tags["error"] = f"{exc_type.__name__}: {exc_val}"
