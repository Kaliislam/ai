"""Ruflo Plugin Bridge — TurkishJARVIS adaptation layer.

This package ports core Ruflo plugin concepts (TypeScript/Node.js)
into practical Python modules. Each module is self-contained and can
be imported independently.

Modules
-------
browser           — Browser automation (wraps Playwright)
rag_memory        — RAG + episodic memory bridge
knowledge_graph_v2 — Enhanced graph memory with reasoning
swarm             — Lightweight multi-agent orchestration
autopilot         — Autonomous task execution loop
goals             — Goal management (integrates project_manager)
intelligence      — Decision engine / reasoning module
observability     — Metrics, logging, tracing
security_audit    — Security scan & audit
sparc             — SPARC architecture assistant
loop_workers      — Periodic worker / task scheduler
market_data       — Market data ingestion (yfinance, free APIs)
"""

__version__ = "0.1.0"

from .browser import RufloBrowser
from .rag_memory import RufloRAGMemory
from .knowledge_graph_v2 import RufloKnowledgeGraph
from .swarm import RufloSwarm
from .autopilot import RufloAutopilot
from .goals import RufloGoals
from .intelligence import RufloIntelligence
from .observability import RufloObservability
from .security_audit import RufloSecurityAudit
from .sparc import RufloSparc
from .loop_workers import RufloLoopWorkers
from .market_data import RufloMarketData

__all__ = [
    "RufloBrowser",
    "RufloRAGMemory",
    "RufloKnowledgeGraph",
    "RufloSwarm",
    "RufloAutopilot",
    "RufloGoals",
    "RufloIntelligence",
    "RufloObservability",
    "RufloSecurityAudit",
    "RufloSparc",
    "RufloLoopWorkers",
    "RufloMarketData",
]
