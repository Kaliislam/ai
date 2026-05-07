"""Ruflo Market Data Plugin Bridge.

Piyasa verisi toplama: yfinance, free crypto APIs, ve basit
聚合 (aggregation) katmanı. Harici API çağrıları async aiohttp
ile yapılır; yfinance sync fallback olarak çalışır.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class MarketSnapshot:
    """Tekil enstrüman snapshot'ı."""

    symbol: str
    price: Optional[float] = None
    change_pct: Optional[float] = None
    volume: Optional[int] = None
    timestamp: str = ""
    source: str = ""
    extra: Dict[str, Any] = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.extra is None:
            self.extra = {}
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


# ---------------------------------------------------------------------------
# Bridge
# ---------------------------------------------------------------------------


class RufloMarketData:
    """Market data ingestion inspired by ruflo-market-data.

    Usage
    -----
    md = RufloMarketData()
    snap = await md.get_stock("AAPL")
    snaps = await md.batch_stocks(["AAPL", "TSLA", "MSFT"])
    crypto = await md.get_crypto("BTC", "USD")
    """

    def __init__(self, cache_ttl_sec: float = 60.0) -> None:
        self.cache_ttl_sec = cache_ttl_sec
        self._cache: Dict[str, tuple[float, MarketSnapshot]] = {}

    # ------------------------------------------------------------------
    # Stock (yfinance primary, async fallback)
    # ------------------------------------------------------------------

    def get_stock_sync(self, symbol: str) -> MarketSnapshot:
        """Synchronous stock fetch via yfinance."""
        try:
            import yfinance as yf
        except ImportError as exc:
            raise RuntimeError("yfinance is required for stock data") from exc

        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period="1d")
        price: Optional[float] = None
        change_pct: Optional[float] = None
        if not hist.empty:
            price = float(hist["Close"].iloc[-1])
            if len(hist) > 1:
                prev = float(hist["Close"].iloc[-2])
                change_pct = round(((price - prev) / prev) * 100, 2) if prev else 0.0

        return MarketSnapshot(
            symbol=symbol,
            price=price or info.get("currentPrice"),
            change_pct=change_pct,
            volume=info.get("volume"),
            source="yfinance",
        )

    async def get_stock(self, symbol: str) -> MarketSnapshot:
        """Async wrapper: tries cache, then thread-pool yfinance."""
        cached = self._from_cache(symbol)
        if cached:
            return cached
        loop = asyncio.get_event_loop()
        snap = await loop.run_in_executor(None, self.get_stock_sync, symbol)
        self._to_cache(symbol, snap)
        return snap

    async def batch_stocks(self, symbols: List[str]) -> List[MarketSnapshot]:
        """Fetch multiple stocks concurrently."""
        return await asyncio.gather(*(self.get_stock(s) for s in symbols))

    # ------------------------------------------------------------------
    # Crypto (free API)
    # ------------------------------------------------------------------

    async def get_crypto(self, coin: str, currency: str = "USD") -> MarketSnapshot:
        """Fetch crypto price from CoinGecko public API."""
        cached = self._from_cache(f"{coin}-{currency}")
        if cached:
            return cached

        url = (
            f"https://api.coingecko.com/api/v3/simple/price"
            f"?ids={coin.lower()}&vs_currencies={currency.lower()}"
            f"&include_24hr_change=true"
        )
        try:
            import aiohttp
        except ImportError as exc:
            raise RuntimeError("aiohttp is required for crypto async fetch") from exc

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()

        coin_data = data.get(coin.lower(), {})
        price = coin_data.get(currency.lower())
        change = coin_data.get(f"{currency.lower()}_24h_change")
        snap = MarketSnapshot(
            symbol=f"{coin.upper()}/{currency.upper()}",
            price=price,
            change_pct=round(change, 2) if change else None,
            source="coingecko",
        )
        self._to_cache(f"{coin}-{currency}", snap)
        return snap

    async def batch_crypto(self, coins: List[str], currency: str = "USD") -> List[MarketSnapshot]:
        """Fetch multiple crypto prices concurrently (rate-limited friendly)."""
        results: List[MarketSnapshot] = []
        for coin in coins:
            try:
                results.append(await self.get_crypto(coin, currency))
            except Exception as exc:
                logger.warning("[ruflo-market-data] crypto %s failed: %s", coin, exc)
                results.append(
                    MarketSnapshot(symbol=f"{coin.upper()}/{currency.upper()}", source="error")
                )
            # CoinGecko free tier rate limit polite pause
            await asyncio.sleep(0.6)
        return results

    # ------------------------------------------------------------------
    # Forex (free API fallback)
    # ------------------------------------------------------------------

    async def get_forex(self, base: str, target: str) -> MarketSnapshot:
        """Fetch forex rate from exchangerate-api.com (free, no key)."""
        pair = f"{base.upper()}-{target.upper()}"
        cached = self._from_cache(pair)
        if cached:
            return cached

        url = f"https://api.exchangerate-api.com/v4/latest/{base.upper()}"
        try:
            import aiohttp
        except ImportError as exc:
            raise RuntimeError("aiohttp is required") from exc

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()

        rates = data.get("rates", {})
        price = rates.get(target.upper())
        snap = MarketSnapshot(symbol=pair, price=price, source="exchangerate-api")
        self._to_cache(pair, snap)
        return snap

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------

    def portfolio_value(
        self, holdings: Dict[str, float], snapshots: List[MarketSnapshot]
    ) -> Dict[str, Any]:
        """Calculate portfolio value from holdings + snapshots.

        ``holdings`` = {symbol: quantity}
        """
        price_map = {s.symbol: s.price for s in snapshots if s.price}
        total = 0.0
        breakdown: Dict[str, Any] = {}
        for symbol, qty in holdings.items():
            price = price_map.get(symbol, 0.0)
            value = round(price * qty, 2) if price else None
            breakdown[symbol] = {"qty": qty, "price": price, "value": value}
            if value:
                total += value
        return {"total_value": round(total, 2), "breakdown": breakdown}

    # ------------------------------------------------------------------
    # Cache
    # ------------------------------------------------------------------

    def _from_cache(self, key: str) -> Optional[MarketSnapshot]:
        import time

        entry = self._cache.get(key)
        if entry is None:
            return None
        ts, snap = entry
        if time.time() - ts > self.cache_ttl_sec:
            self._cache.pop(key, None)
            return None
        return snap

    def _to_cache(self, key: str, snap: MarketSnapshot) -> None:
        import time

        self._cache[key] = (time.time(), snap)

    def clear_cache(self) -> None:
        self._cache.clear()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def summary(self) -> Dict[str, Any]:
        return {
            "cache_entries": len(self._cache),
            "cache_ttl_sec": self.cache_ttl_sec,
        }
