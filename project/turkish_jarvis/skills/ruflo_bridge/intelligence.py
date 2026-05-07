"""Ruflo Intelligence Plugin Bridge.

Karar verme motoru: mevcut durumu değerlendirir, aksiyon önerileri üretir,
ve basit bir oylama (voting) mekanizmasıyla çoklu strateji arasından
seçim yapar. LLM-agnostik; stratejiler fonksiyon olarak inject edilir.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class ActionProposal:
    """Bir aksiyon önerisi."""

    action: str
    confidence: float  # 0.0 - 1.0
    reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Decision:
    """Motorun nihai kararı."""

    chosen_action: str
    proposals: List[ActionProposal]
    strategy_used: str
    confidence: float


# ---------------------------------------------------------------------------
# Bridge
# ---------------------------------------------------------------------------


class RufloIntelligence:
    """Lightweight decision engine inspired by ruflo-intelligence.

    Usage
    -----
    intel = RufloIntelligence()
    intel.register_strategy("greedy", greedy_fn)
    intel.register_strategy("safe", safe_fn)
    decision = intel.decide(state, method="vote")
    """

    def __init__(self, default_method: str = "best") -> None:
        self.default_method = default_method
        self.strategies: Dict[str, Callable[[Dict[str, Any]], List[ActionProposal]]] = {}
        self._history: List[Decision] = []

    # ------------------------------------------------------------------
    # Strategy registry
    # ------------------------------------------------------------------

    def register_strategy(
        self,
        name: str,
        strategy: Callable[[Dict[str, Any]], List[ActionProposal]],
    ) -> None:
        """Register a callable strategy.

        A strategy receives a ``state`` dict and returns a list of
        ``ActionProposal`` objects.
        """
        self.strategies[name] = strategy
        logger.info("[ruflo-intelligence] strategy '%s' registered", name)

    def unregister_strategy(self, name: str) -> bool:
        return self.strategies.pop(name, None) is not None

    # ------------------------------------------------------------------
    # Decision core
    # ------------------------------------------------------------------

    def decide(
        self,
        state: Dict[str, Any],
        method: Optional[str] = None,
        strategy_filter: Optional[List[str]] = None,
    ) -> Decision:
        """Evaluate all registered strategies and return a decision.

        Parameters
        ----------
        state : dict
            Current world / task state.
        method : str
            ``best`` — pick highest-confidence proposal globally.  \n
            ``vote`` — each strategy votes for its best; majority wins.  \n            ``random_weighted`` — sample proportional to confidence.
        strategy_filter : list
            Run only these strategy names.

        Returns
        -------
        ``Decision`` object.
        """
        method = method or self.default_method
        active = strategy_filter or list(self.strategies.keys())

        all_proposals: List[ActionProposal] = []
        per_strategy: Dict[str, List[ActionProposal]] = {}

        for name in active:
            fn = self.strategies.get(name)
            if fn is None:
                continue
            try:
                proposals = fn(state)
                per_strategy[name] = proposals
                all_proposals.extend(proposals)
            except Exception as exc:
                logger.warning("[ruflo-intelligence] strategy '%s' failed: %s", name, exc)

        if not all_proposals:
            decision = Decision(
                chosen_action="noop",
                proposals=[],
                strategy_used="none",
                confidence=0.0,
            )
            self._history.append(decision)
            return decision

        chosen: str
        conf: float

        if method == "best":
            best = max(all_proposals, key=lambda p: p.confidence)
            chosen = best.action
            conf = best.confidence
        elif method == "vote":
            votes: Dict[str, float] = {}
            for proposals in per_strategy.values():
                if proposals:
                    top = max(proposals, key=lambda p: p.confidence)
                    votes[top.action] = votes.get(top.action, 0.0) + top.confidence
            chosen = max(votes, key=votes.get)  # type: ignore[arg-type]
            conf = votes[chosen] / sum(votes.values()) if votes else 0.0
        elif method == "random_weighted":
            total_conf = sum(p.confidence for p in all_proposals)
            if total_conf == 0:
                chosen = random.choice(all_proposals).action
                conf = 0.0
            else:
                r = random.uniform(0, total_conf)
                cumulative = 0.0
                for p in all_proposals:
                    cumulative += p.confidence
                    if cumulative >= r:
                        chosen = p.action
                        conf = p.confidence
                        break
                else:
                    chosen = all_proposals[-1].action
                    conf = all_proposals[-1].confidence
        else:
            raise ValueError(f"Unknown decision method: {method}")

        decision = Decision(
            chosen_action=chosen,
            proposals=all_proposals,
            strategy_used=method,
            confidence=round(conf, 3),
        )
        self._history.append(decision)
        logger.info(
            "[ruflo-intelligence] decision=%s confidence=%.2f method=%s",
            chosen, conf, method,
        )
        return decision

    # ------------------------------------------------------------------
    # Reflection helpers
    # ------------------------------------------------------------------

    def get_history(self, limit: int = 50) -> List[Decision]:
        """Return recent decisions."""
        return self._history[-limit:]

    def most_common_action(self, limit: int = 50) -> Optional[str]:
        """Most frequently chosen action in recent history."""
        from collections import Counter

        actions = [d.chosen_action for d in self._history[-limit:]]
        if not actions:
            return None
        return Counter(actions).most_common(1)[0][0]

    def confidence_trend(self, window: int = 10) -> Dict[str, float]:
        """Average confidence over recent windows."""
        recent = self._history[-window:]
        if not recent:
            return {"mean": 0.0, "min": 0.0, "max": 0.0}
        confs = [d.confidence for d in recent]
        return {
            "mean": round(sum(confs) / len(confs), 3),
            "min": round(min(confs), 3),
            "max": round(max(confs), 3),
        }

    # ------------------------------------------------------------------
    # Built-in demo strategies
    # ------------------------------------------------------------------

    @staticmethod
    def demo_strategies() -> Dict[str, Callable[[Dict[str, Any]], List[ActionProposal]]]:
        """Return two trivial strategies for quick testing."""

        def greedy(state: Dict[str, Any]) -> List[ActionProposal]:
            score = state.get("score", 0)
            return [
                ActionProposal("increase", 0.8, "Maximize score"),
                ActionProposal("hold", 0.2, "Conservative"),
            ]

        def safe(state: Dict[str, Any]) -> List[ActionProposal]:
            risk = state.get("risk", 0.5)
            if risk > 0.7:
                return [
                    ActionProposal("retreat", 0.9, "High risk detected"),
                    ActionProposal("hold", 0.1, "Wait"),
                ]
            return [
                ActionProposal("advance", 0.7, "Risk is acceptable"),
                ActionProposal("hold", 0.3, "Stay cautious"),
            ]

        return {"greedy": greedy, "safe": safe}
