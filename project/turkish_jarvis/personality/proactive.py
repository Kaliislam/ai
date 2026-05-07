"""Proactive behaviour engine for Turkish JARVIS.

Provides time-based triggers, conversation-based preference learning,
and periodic proactive suggestions so the assistant feels alive and
attentive rather than purely reactive.
"""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from typing import Any, Callable


@dataclass
class Trigger:
    """A single proactive trigger definition."""

    trigger_id: str
    label: str
    condition: Callable[["ProactiveEngine", str], bool]
    action: Callable[["ProactiveEngine", str], str | None]
    cooldown_minutes: int = 60
    last_fired: datetime | None = None


@dataclass
class LearnedPreference:
    """A preference extracted from natural conversation."""

    key: str
    value: str
    confidence: float = 1.0
    source_message: str = ""
    learned_at: datetime = field(default_factory=datetime.now)


class ProactiveEngine:
    """Drives proactive suggestions, routines, and preference learning.

    The engine is designed to be called periodically (e.g. every minute
    by a background task). It evaluates *triggers* and returns suggestions
    that the caller may choose to surface to the user.
    """

    # ------------------------------------------------------------------ #
    # Preference-extraction regex patterns (Turkish + English)
    # ------------------------------------------------------------------ #
    PREFERENCE_PATTERNS: list[tuple[str, str, float]] = [
        # Turkish positive preferences
        (r"(?i)(\w+)\s+(seviyorum|seviyorum|çok\s+seviyorum|bayılıyorum)", "likes", 0.9),
        (r"(?i)(\w+)\s+(sevmiyorum|nefret\s+ediyorum|hiç\s+sevmem)", "dislikes", 0.9),
        (r"(?i)(\w+)\s+(isterim|istiyorum|ricam|rica\s+ederim)", "wants", 0.8),
        (r"(?i)(her\s+gün|sabahları|akşamları|öğlenleri)\s+(.*?)(?:yaparım|yapıyorum|ederim)", "routine", 0.7),
        (r"(?i)adım\s+(\w+)", "name", 1.0),
        (r"(?i)ismim\s+(\w+)", "name", 1.0),
        # English positive preferences
        (r"(?i)i\s+(love|like|enjoy)\s+(\w+)", "likes", 0.9),
        (r"(?i)i\s+(hate|dislike|can't\s+stand)\s+(\w+)", "dislikes", 0.9),
        (r"(?i)i\s+(want|would\s+like|need)\s+(\w+)", "wants", 0.8),
        (r"(?i)my\s+name\s+is\s+(\w+)", "name", 1.0),
        (r"(?i)call\s+me\s+(\w+)", "name", 1.0),
    ]

    # ------------------------------------------------------------------ #
    # Time-based routine windows
    # ------------------------------------------------------------------ #
    ROUTINE_WINDOWS: dict[str, tuple[time, time]] = {
        "morning": (time(6, 0), time(10, 0)),
        "noon": (time(11, 30), time(13, 30)),
        "evening": (time(17, 0), time(20, 0)),
        "night": (time(21, 0), time(23, 59)),
    }

    def __init__(self, locale: str = "tr") -> None:
        """Initialise the proactive engine.

        Args:
            locale: Default language for suggestion messages (``'tr'`` or ``'en'``).
        """
        self.locale = locale
        self._lock = threading.RLock()
        self._triggers: list[Trigger] = []
        self._preferences: dict[str, list[LearnedPreference]] = {}
        self._session_state: dict[str, dict[str, Any]] = {}
        self._register_default_triggers()

    # ================================================================= #
    # Internal: default triggers
    # ================================================================= #

    def _register_default_triggers(self) -> None:
        """Register the built-in time-based and idle triggers."""
        # Morning routine
        self.add_trigger(
            trigger_id="morning_routine",
            label="Sabah rutini / Morning routine",
            condition=lambda eng, sid: eng._is_in_window("morning") and not eng._session_flag(sid, "morning_done"),
            action=lambda eng, sid: eng._set_session_flag(sid, "morning_done", True) or eng._greeting_for("morning"),
            cooldown_minutes=360,
        )
        # Noon reminder
        self.add_trigger(
            trigger_id="noon_break",
            label="Öğle molası / Noon break",
            condition=lambda eng, sid: eng._is_in_window("noon") and not eng._session_flag(sid, "noon_done"),
            action=lambda eng, sid: eng._set_session_flag(sid, "noon_done", True) or eng._greeting_for("noon"),
            cooldown_minutes=360,
        )
        # Evening wrap-up
        self.add_trigger(
            trigger_id="evening_wrap",
            label="Akşam özeti / Evening wrap-up",
            condition=lambda eng, sid: eng._is_in_window("evening") and not eng._session_flag(sid, "evening_done"),
            action=lambda eng, sid: eng._set_session_flag(sid, "evening_done", True) or eng._greeting_for("evening"),
            cooldown_minutes=360,
        )
        # Idle prompt (fires if >30 min silent during the day)
        self.add_trigger(
            trigger_id="idle_prompt",
            label="Boşta öneri / Idle suggestion",
            condition=lambda eng, sid: eng._is_idle(sid, minutes=30) and eng._session_flag(sid, "last_idle") is None,
            action=lambda eng, sid: (
                eng._set_session_flag(sid, "last_idle", datetime.now()) or eng._greeting_for("idle")
            ),
            cooldown_minutes=30,
        )

    # ================================================================= #
    # Public API: trigger management
    # ================================================================= #

    def add_trigger(
        self,
        trigger_id: str,
        label: str,
        condition: Callable[["ProactiveEngine", str], bool],
        action: Callable[["ProactiveEngine", str], str | None],
        cooldown_minutes: int = 60,
    ) -> None:
        """Register a new proactive trigger.

        Args:
            trigger_id: Unique identifier for the trigger.
            label: Human-readable label.
            condition: Callable ``(engine, session_id) -> bool``.
            action: Callable ``(engine, session_id) -> str | None``.
            cooldown_minutes: Minimum minutes between consecutive firings.
        """
        with self._lock:
            # Remove old trigger with same ID if present
            self._triggers = [t for t in self._triggers if t.trigger_id != trigger_id]
            self._triggers.append(
                Trigger(
                    trigger_id=trigger_id,
                    label=label,
                    condition=condition,
                    action=action,
                    cooldown_minutes=cooldown_minutes,
                )
            )

    def remove_trigger(self, trigger_id: str) -> bool:
        """Remove a trigger by ID.

        Returns:
            ``True`` if the trigger existed and was removed.
        """
        with self._lock:
            before = len(self._triggers)
            self._triggers = [t for t in self._triggers if t.trigger_id != trigger_id]
            return len(self._triggers) < before

    # ================================================================= #
    # Public API: periodic check
    # ================================================================= #

    def check_triggers(
        self, session_id: str, last_message_time: datetime | None = None
    ) -> list[dict[str, Any]]:
        """Evaluate all triggers for a session and return those that fire.

        Args:
            session_id: Session identifier.
            last_message_time: Timestamp of the user's last message (used for idle detection).

        Returns:
            List of fired trigger dictionaries with ``trigger_id``, ``label``,
            and ``message`` keys.
        """
        fired: list[dict[str, Any]] = []
        now = datetime.now()

        with self._lock:
            # Store last message time for idle calculations
            if last_message_time is not None:
                self._set_session_flag(session_id, "last_message_time", last_message_time)

            for trig in self._triggers:
                # Cooldown check
                if trig.last_fired is not None:
                    elapsed = (now - trig.last_fired).total_seconds() / 60.0
                    if elapsed < trig.cooldown_minutes:
                        continue

                # Condition check
                try:
                    if not trig.condition(self, session_id):
                        continue
                except Exception:
                    continue  # Silently skip broken triggers

                # Action execution
                try:
                    message = trig.action(self, session_id)
                except Exception:
                    message = None

                if message:
                    trig.last_fired = now
                    fired.append(
                        {
                            "trigger_id": trig.trigger_id,
                            "label": trig.label,
                            "message": message,
                            "fired_at": now.isoformat(),
                        }
                    )

        return fired

    def get_proactive_suggestion(self, session_id: str) -> str | None:
        """Return the *first* available proactive suggestion for a session.

        This is a convenience wrapper around :py:meth:`check_triggers`.

        Args:
            session_id: Session identifier.

        Returns:
            Suggestion text, or ``None`` if no trigger fired.
        """
        results = self.check_triggers(session_id)
        return results[0]["message"] if results else None

    # ================================================================= #
    # Public API: preference learning
    # ================================================================= #

    def learn_from_message(self, session_id: str, message: str) -> list[LearnedPreference]:
        """Extract preferences from a raw user message.

        Args:
            session_id: Session identifier.
            message: Raw user text.

        Returns:
            List of newly learned preferences.
        """
        learned: list[LearnedPreference] = []
        with self._lock:
            for pattern, category, confidence in self.PREFERENCE_PATTERNS:
                for match in re.finditer(pattern, message):
                    # Use the last capturing group as the value
                    groups = match.groups()
                    value = groups[-1] if groups else match.group(0)
                    pref = LearnedPreference(
                        key=category,
                        value=value.strip(),
                        confidence=confidence,
                        source_message=message,
                    )
                    self._preferences.setdefault(session_id, []).append(pref)
                    learned.append(pref)
        return learned

    def get_learned_preferences(self, session_id: str) -> dict[str, list[str]]:
        """Return aggregated learned preferences for a session.

        Args:
            session_id: Session identifier.

        Returns:
            Dictionary ``{category: [value, …]}``.
        """
        with self._lock:
            prefs = self._preferences.get(session_id, [])
        result: dict[str, list[str]] = {}
        for p in prefs:
            result.setdefault(p.key, []).append(p.value)
        return result

    def get_learned_preferences_detailed(self, session_id: str) -> list[LearnedPreference]:
        """Return the full list of learned preferences with metadata."""
        with self._lock:
            return list(self._preferences.get(session_id, []))

    def clear_preferences(self, session_id: str) -> None:
        """Clear all learned preferences for a session."""
        with self._lock:
            self._preferences.pop(session_id, None)

    # ================================================================= #
    # Helpers: session state
    # ================================================================= #

    def _session_flag(self, session_id: str, key: str) -> Any:
        """Retrieve a session flag value (``None`` if absent)."""
        with self._lock:
            return self._session_state.get(session_id, {}).get(key)

    def _set_session_flag(self, session_id: str, key: str, value: Any) -> None:
        """Set a session flag value."""
        with self._lock:
            self._session_state.setdefault(session_id, {})[key] = value

    def _is_in_window(self, window_name: str) -> bool:
        """Check whether the current local time falls inside a named routine window."""
        start, end = self.ROUTINE_WINDOWS.get(window_name, (time.min, time.max))
        now = datetime.now().time()
        if start <= end:
            return start <= now <= end
        # Wraps past midnight (not used by current windows, but future-proof)
        return now >= start or now <= end

    def _is_idle(self, session_id: str, minutes: int = 30) -> bool:
        """Return ``True`` if the session has been idle for at least *minutes*."""
        last = self._session_flag(session_id, "last_message_time")
        if last is None:
            return False
        if isinstance(last, str):
            last = datetime.fromisoformat(last)
        return (datetime.now() - last).total_seconds() >= minutes * 60

    def _greeting_for(self, occasion: str) -> str | None:
        """Return a locale-aware greeting string for a given occasion."""
        if self.locale == "tr":
            mapping = {
                "morning": "Günaydın efendim. Bugünkü planlarınızı duymak isterim; size nasıl yardımcı olabilirim?",
                "noon": "Öğle vaktine geldik efendim. Kısa bir mola öneririm; belki hava durumuna veya öğle menüsüne bakmak istersiniz?",
                "evening": "İyi akşamlar efendim. Günün özeti veya yarın için bir planlama yapmamı ister misiniz?",
                "night": "Geç saat oldu efendim. Dinlenmeyi düşünebilirsiniz; ışıkları kısmamı veya yarın için alarm kurmamı ister misiniz?",
                "idle": "Uzun süredir sessizsiniz efendim. Yardıma ihtiyacınız olup olmadığını kontrol etmek istedim.",
            }
        else:
            mapping = {
                "morning": "Good morning sir. I would love to hear today's plans; how may I assist?",
                "noon": "It is noon sir. I suggest a short break; perhaps a weather check or lunch menu?",
                "evening": "Good evening sir. Would you like a daily summary or help planning tomorrow?",
                "night": "It is quite late sir. You may want to rest; shall I dim the lights or set a morning alarm?",
                "idle": "You have been quiet for a while sir. I wanted to check if you need assistance.",
            }
        return mapping.get(occasion)
