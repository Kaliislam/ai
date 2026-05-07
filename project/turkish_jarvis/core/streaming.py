"""Streaming response pipeline.

Buffers LLM text chunks, detects completed sentences, and forwards
them to a TTS engine in real-time. Also supports WebSocket broadcasting
of incremental tokens.

Architecture:
    LLM chunks ──► SentenceBuffer ──► TTS enqueue ──► Audio out
                           │
                           └─► WebSocket broadcast (optional)
"""

from __future__ import annotations

import asyncio
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Coroutine, Dict, List, Optional, Protocol

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Protocols / ABCs
# ---------------------------------------------------------------------------


class TTSBackend(Protocol):
    """Protocol for a TTS backend that accepts text and returns audio."""

    async def synthesize(self, text: str) -> bytes:
        ...


class SentenceSplitter(ABC):
    """Abstract sentence boundary detector."""

    @abstractmethod
    def split(self, text: str) -> List[str]:
        """Return a list of complete sentences."""

    @abstractmethod
    def remaining(self, text: str) -> str:
        """Return the trailing incomplete fragment."""


# ---------------------------------------------------------------------------
# Default implementations
# ---------------------------------------------------------------------------


class RegexSentenceSplitter(SentenceSplitter):
    """Sentence splitter using regex for Turkish and generic punctuation.

    Handles abbreviations and common Turkish endings (e.g. "vb.", "dr.", "prof.")
    to avoid false splits.
    """

    ABBREVIATIONS = {"dr", "prof", "doç", "vb", "vs", "vb.", "vs.", "b.", "m.", "sayın", "bay", "bayan"}

    def __init__(self) -> None:
        # Match sentence endings: . ! ? followed by space or end
        self._pattern = re.compile(r'(?<=[.!?])\s+')
        # Cleaner: strip trailing whitespace
        self._trim = re.compile(r'\s+')

    def split(self, text: str) -> List[str]:
        raw = self._pattern.split(text.strip())
        sentences: List[str] = []
        for candidate in raw:
            candidate = candidate.strip()
            if not candidate:
                continue
            # Merge if last token looks like an abbreviation
            if sentences and self._is_abbreviation_fragment(sentences[-1]):
                sentences[-1] = sentences[-1] + " " + candidate
            else:
                sentences.append(candidate)
        # Post-filter: any sentence that ends with an abbreviation gets merged with next
        merged: List[str] = []
        for s in sentences:
            if merged and self._ends_with_abbreviation(merged[-1]):
                merged[-1] = merged[-1] + " " + s
            else:
                merged.append(s)
        return merged

    def remaining(self, text: str) -> str:
        sentences = self.split(text)
        if not sentences:
            return text.strip()
        # The remaining fragment is whatever is not covered by complete sentences
        combined = " ".join(sentences)
        if text.strip().startswith(combined):
            remainder = text.strip()[len(combined):].strip()
            return remainder
        # Fallback: return last sentence if it lacks terminal punctuation
        last = sentences[-1]
        if not last.endswith((".", "!", "?")):
            return last
        return ""

    @classmethod
    def _is_abbreviation_fragment(cls, text: str) -> bool:
        # If previous text ended mid-abbreviation
        words = text.lower().split()
        if not words:
            return False
        return words[-1].rstrip(".") in cls.ABBREVIATIONS

    @classmethod
    def _ends_with_abbreviation(cls, text: str) -> bool:
        words = text.lower().split()
        if not words:
            return False
        last = words[-1].rstrip(".")
        return last in cls.ABBREVIATIONS


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------


@dataclass
class StreamChunk:
    """A chunk in the streaming pipeline."""

    text: str
    is_sentence: bool = False
    is_final: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class StreamingPipeline:
    """Sentence-level streaming pipeline from LLM chunks to TTS.

    Usage:
        pipeline = StreamingPipeline(tts_backend=my_tts)
        await pipeline.start()
        async for chunk in llm_stream:
            await pipeline.feed(chunk)
        await pipeline.finalize()
    """

    def __init__(
        self,
        tts_backend: Optional[TTSBackend] = None,
        sentence_splitter: Optional[SentenceSplitter] = None,
        on_sentence: Optional[Callable[[str], Coroutine[Any, Any, None]]] = None,
        on_token: Optional[Callable[[str], Coroutine[Any, Any, None]]] = None,
        max_buffer_chars: int = 2000,
    ) -> None:
        self.tts_backend = tts_backend
        self.splitter = sentence_splitter or RegexSentenceSplitter()
        self.on_sentence = on_sentence
        self.on_token = on_token
        self.max_buffer_chars = max_buffer_chars
        self._buffer = ""
        self._queue: asyncio.Queue[StreamChunk] = asyncio.Queue()
        self._tts_queue: asyncio.Queue[str] = asyncio.Queue()
        self._task: Optional[asyncio.Task[None]] = None
        self._tts_task: Optional[asyncio.Task[None]] = None
        self._running = False
        self._websocket_clients: List[Any] = []

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start background processing tasks."""
        self._running = True
        self._task = asyncio.create_task(self._process_loop())
        if self.tts_backend is not None:
            self._tts_task = asyncio.create_task(self._tts_loop())

    async def stop(self) -> None:
        """Stop background tasks gracefully."""
        self._running = False
        await self._queue.put(StreamChunk(text="", is_final=True))
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except asyncio.TimeoutError:
                self._task.cancel()
        if self._tts_task:
            self._tts_queue.put_nowait("")
            try:
                await asyncio.wait_for(self._tts_task, timeout=10.0)
            except asyncio.TimeoutError:
                self._tts_task.cancel()

    # ------------------------------------------------------------------
    # Feeding
    # ------------------------------------------------------------------

    async def feed(self, text_chunk: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Feed a raw LLM text chunk into the pipeline."""
        if not self._running:
            raise RuntimeError("Pipeline not started")
        await self._queue.put(
            StreamChunk(text=text_chunk, metadata=metadata or {})
        )

    async def finalize(self) -> None:
        """Flush remaining buffer as a final sentence."""
        await self._queue.put(StreamChunk(text="", is_final=True))
        if self._task:
            await self._task

    # ------------------------------------------------------------------
    # Processing loops
    # ------------------------------------------------------------------

    async def _process_loop(self) -> None:
        while self._running:
            chunk = await self._queue.get()
            if chunk.is_final:
                # Flush remaining buffer
                if self._buffer.strip():
                    await self._emit_sentence(self._buffer.strip())
                self._buffer = ""
                break
            self._buffer += chunk.text
            if len(self._buffer) > self.max_buffer_chars:
                # Safety flush if buffer grows too large
                await self._emit_sentence(self._buffer.strip())
                self._buffer = ""
                continue
            sentences = self.splitter.split(self._buffer)
            # All but the last are complete sentences
            for sentence in sentences[:-1]:
                await self._emit_sentence(sentence)
            # Keep the last fragment (may be incomplete)
            self._buffer = sentences[-1] if sentences else self._buffer
            # Token callback for real-time UI updates
            if self.on_token:
                await self.on_token(chunk.text)

    async def _emit_sentence(self, sentence: str) -> None:
        sentence = sentence.strip()
        if not sentence:
            return
        logger.debug("Emitting sentence: %s", sentence[:60])
        if self.on_sentence:
            await self.on_sentence(sentence)
        # Enqueue for TTS
        if self.tts_backend is not None:
            await self._tts_queue.put(sentence)
        # WebSocket broadcast
        await self._broadcast_ws({"type": "sentence", "text": sentence})

    async def _tts_loop(self) -> None:
        """Consume sentences and synthesize audio."""
        while self._running:
            sentence = await self._tts_queue.get()
            if not sentence:
                break
            try:
                audio = await self.tts_backend.synthesize(sentence)
                await self._broadcast_ws({
                    "type": "audio",
                    "format": "mp3",
                    "data": audio.hex()[:80] + "...",  # placeholder for binary
                })
            except Exception as exc:
                logger.error("TTS synthesis failed: %s", exc)

    # ------------------------------------------------------------------
    # WebSocket helpers
    # ------------------------------------------------------------------

    def attach_websocket(self, ws: Any) -> None:
        """Attach a WebSocket connection (e.g. aiohttp WS or FastAPI WS)."""
        self._websocket_clients.append(ws)

    def detach_websocket(self, ws: Any) -> None:
        """Detach a WebSocket connection."""
        if ws in self._websocket_clients:
            self._websocket_clients.remove(ws)

    async def _broadcast_ws(self, message: Dict[str, Any]) -> None:
        """Send JSON message to all attached WebSocket clients."""
        dead: List[Any] = []
        for ws in self._websocket_clients:
            try:
                # Support both aiohttp and generic send_json
                if hasattr(ws, "send_json"):
                    await ws.send_json(message)
                elif hasattr(ws, "send_str"):
                    await ws.send_str(json.dumps(message, ensure_ascii=False))
                elif hasattr(ws, "send"):
                    await ws.send(json.dumps(message, ensure_ascii=False))
            except Exception as exc:
                logger.debug("WS broadcast error: %s", exc)
                dead.append(ws)
        for ws in dead:
            self.detach_websocket(ws)

    # ------------------------------------------------------------------
    # Convenience generator
    # ------------------------------------------------------------------

    @classmethod
    async def stream_from_llm(
        cls,
        llm_chunks: AsyncIterator[str],
        tts_backend: Optional[TTSBackend] = None,
        on_sentence: Optional[Callable[[str], Coroutine[Any, Any, None]]] = None,
    ) -> List[str]:
        """High-level helper: feed an LLM async iterator and collect sentences."""
        pipeline = cls(tts_backend=tts_backend, on_sentence=on_sentence)
        sentences: List[str] = []
        await pipeline.start()
        try:
            async for chunk in llm_chunks:
                await pipeline.feed(chunk)
            await pipeline.finalize()
        finally:
            await pipeline.stop()
        # Collect from internal history not kept; use callback instead.
        return sentences

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "StreamingPipeline":
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Any],
        exc_val: Optional[Any],
        exc_tb: Optional[Any],
    ) -> None:
        await self.stop()
