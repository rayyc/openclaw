# backend/agents/tools/news_tool.py
"""
Forex news and sentiment tool.
Uses SerpAPI (Google Search) for news and event detection.

DESIGN: Called ONCE per trading engine run with symbol="" to get
general market sentiment. Per-symbol sentiment is not worth the
SerpAPI cost — general market direction is sufficient for trading decisions.
"""
from datetime import datetime, timezone
from backend.agents.tools.google_search import google_search


async def get_forex_news(symbol: str = "") -> dict:
    """
    Get current forex market news and sentiment.

    For trading efficiency this returns GENERAL market sentiment
    rather than per-symbol sentiment. This saves SerpAPI credits
    while still giving Claude the context it needs.

    Args:
        symbol: Currency pair — used only to check currency-specific
                high-impact events. Sentiment is always general.

    Returns:
        dict with events, safety flag, sentiment score
    """
    result: dict = {
        "success":                     True,
        "symbol":                      symbol,
        "upcoming_events":             [],
        "high_impact_soon":            False,
        "minutes_to_next_high_impact": None,
        "sentiment":                   "neutral",
        "sentiment_score":             50,
        "news_headlines":              [],
        "safe_to_trade":               True,
        "reason":                      "",
        "error":                       None
    }

    try:
        today = datetime.now(tz=timezone.utc).strftime("%B %d %Y")

        # ── Single search: combines event check + sentiment in one query ───────
        search = await google_search(
            query=f"forex market outlook {today} USD EUR GBP",
            num_results=6
        )

        if not search["success"]:
            result["reason"] = "News unavailable — proceeding with caution"
            return result

        headlines:    list[dict] = []
        bullish_words = [
            "bullish", "buy", "rise", "up", "gain", "rally", "strong",
            "positive", "growth", "higher", "surge", "recover", "upside"
        ]
        bearish_words = [
            "bearish", "sell", "fall", "down", "drop", "weak", "decline",
            "negative", "lower", "plunge", "pressure", "downside", "risk"
        ]
        high_impact_words = [
            "nfp", "non-farm", "fomc", "fed decision", "rate decision",
            "cpi", "inflation", "gdp", "unemployment", "payroll"
        ]

        bullish_count    = 0
        bearish_count    = 0
        high_impact_found = False

        for r in search["results"]:
            title    = r.get("title",   "")
            snippet  = r.get("snippet", "")
            combined = (title + " " + snippet).lower()

            headlines.append({
                "title":   title,
                "url":     r.get("url", ""),
                "snippet": snippet[:150]
            })

            # Check for high-impact event keywords
            if any(w in combined for w in high_impact_words):
                high_impact_found = True

            # Sentiment scoring
            for word in bullish_words:
                if word in combined:
                    bullish_count += 1
                    break
            for word in bearish_words:
                if word in combined:
                    bearish_count += 1
                    break

        # ── Sentiment calculation ──────────────────────────────────────────────
        total = bullish_count + bearish_count
        if total > 0:
            bull_pct = round(bullish_count / total * 100)
            if bull_pct >= 65:
                sentiment = "bullish"
            elif bull_pct <= 35:
                sentiment = "bearish"
            else:
                sentiment = "neutral"
            result["sentiment"]       = sentiment
            result["sentiment_score"] = bull_pct

        # ── Safety check ──────────────────────────────────────────────────────
        if high_impact_found:
            result["high_impact_soon"]  = True
            result["safe_to_trade"]     = False
            result["reason"] = "High-impact economic event detected — avoid trading until confirmed"
        else:
            result["reason"] = "No high-impact events detected — safe to trade"

        result["news_headlines"] = headlines[:4]
        return result

    except Exception as e:
        result["error"]         = f"News fetch failed: {str(e)}"
        result["safe_to_trade"] = True
        result["reason"]        = "News check failed — proceeding with caution"
        return result


def extract_currencies(symbol: str) -> list[str]:
    """Extract individual currencies from a forex pair symbol."""
    if not symbol or len(symbol) < 5:
        return []

    symbol = symbol.upper().replace("/", "").replace("-", "").replace("_", "")

    commodity_map: dict[str, list[str]] = {
        "XAUUSD": ["XAU", "USD"],
        "XAGUSD": ["XAG", "USD"],
        "USOIL":  ["USD"],
        "UKOIL":  ["USD"],
    }
    if symbol in commodity_map:
        return commodity_map[symbol]

    if len(symbol) == 6:
        return [symbol[:3], symbol[3:]]

    return []