# backend/agents/tools/ta_tool.py
"""
Technical Analysis tool.
Calculates all indicators from raw candle data.
No external TA library needed — pure Python calculations.
"""
import math
from typing import Optional


def get_pip_multiplier(symbol: str) -> float:
    """
    Return the correct pip multiplier for a given symbol.

    Pip values differ by instrument:
      JPY pairs  (USD/JPY, EUR/JPY etc.) → 1 pip = 0.01  → multiply by 100
      XAU/USD    (Gold)                  → 1 pip = 0.1   → multiply by 10
      XAG/USD    (Silver)                → 1 pip = 0.001 → multiply by 1000
      Oil (WTI/Brent)                    → 1 pip = 0.01  → multiply by 100
      All others (EUR/USD etc.)          → 1 pip = 0.0001→ multiply by 10000
    """
    s = symbol.upper().replace("/", "").replace("-", "").replace("_", "")

    if "JPY" in s:
        return 100.0
    if s in ("XAUUSD", "GOLD"):
        return 10.0
    if s in ("XAGUSD", "SILVER"):
        return 1000.0
    if "OIL" in s or "WTI" in s or "BRENT" in s or "UKOIL" in s or "USOIL" in s:
        return 100.0
    return 10000.0


def calculate_ema(closes: list[float], period: int) -> list[float]:
    """Calculate Exponential Moving Average."""
    if len(closes) < period:
        return []
    k = 2 / (period + 1)
    emas = [sum(closes[:period]) / period]  # seed with SMA
    for price in closes[period:]:
        emas.append(price * k + emas[-1] * (1 - k))
    return emas


def calculate_sma(closes: list[float], period: int) -> list[float]:
    """Calculate Simple Moving Average."""
    if len(closes) < period:
        return []
    return [
        sum(closes[i:i + period]) / period
        for i in range(len(closes) - period + 1)
    ]


def calculate_rsi(closes: list[float], period: int = 14) -> list[float]:
    """Calculate Relative Strength Index."""
    if len(closes) < period + 1:
        return []

    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains  = [d if d > 0 else 0 for d in deltas]
    losses = [abs(d) if d < 0 else 0 for d in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    rsi_values = []
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            rsi_values.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(round(100 - (100 / (1 + rs)), 2))

    return rsi_values


def calculate_macd(
    closes: list[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> dict:
    """Calculate MACD line, signal line, and histogram."""
    if len(closes) < slow + signal:
        return {"macd": [], "signal": [], "histogram": []}

    ema_fast = calculate_ema(closes, fast)
    ema_slow = calculate_ema(closes, slow)

    offset = slow - fast
    macd_line = [
        round(ema_fast[i + offset] - ema_slow[i], 6)
        for i in range(len(ema_slow))
    ]

    signal_line = calculate_ema(macd_line, signal)

    offset2 = len(macd_line) - len(signal_line)
    histogram = [
        round(macd_line[i + offset2] - signal_line[i], 6)
        for i in range(len(signal_line))
    ]

    return {
        "macd":      macd_line,
        "signal":    signal_line,
        "histogram": histogram
    }


def calculate_bollinger_bands(
    closes: list[float],
    period: int = 20,
    std_dev: float = 2.0
) -> dict:
    """Calculate Bollinger Bands (upper, middle, lower)."""
    if len(closes) < period:
        return {"upper": [], "middle": [], "lower": []}

    middle = calculate_sma(closes, period)
    upper  = []
    lower  = []

    for i in range(len(middle)):
        window   = closes[i:i + period]
        mean     = middle[i]
        variance = sum((x - mean) ** 2 for x in window) / period
        std      = math.sqrt(variance)
        upper.append(round(mean + std_dev * std, 5))
        lower.append(round(mean - std_dev * std, 5))

    return {
        "upper":  upper,
        "middle": [round(m, 5) for m in middle],
        "lower":  lower
    }


def calculate_atr(
    highs:  list[float],
    lows:   list[float],
    closes: list[float],
    period: int = 14
) -> list[float]:
    """Calculate Average True Range."""
    if len(closes) < period + 1:
        return []

    true_ranges = []
    for i in range(1, len(closes)):
        high_low   = highs[i] - lows[i]
        high_close = abs(highs[i] - closes[i - 1])
        low_close  = abs(lows[i]  - closes[i - 1])
        true_ranges.append(max(high_low, high_close, low_close))

    atr = [sum(true_ranges[:period]) / period]
    for tr in true_ranges[period:]:
        atr.append(round((atr[-1] * (period - 1) + tr) / period, 6))

    return atr


def find_support_resistance(
    highs:    list[float],
    lows:     list[float],
    closes:   list[float],
    symbol:   str = "",
    lookback: int = 50
) -> dict:
    """
    Find key support and resistance levels from recent price action.
    Uses swing highs and lows method.
    """
    if len(closes) < lookback:
        lookback = len(closes)

    pip_mult     = get_pip_multiplier(symbol)
    recent_highs = highs[-lookback:]
    recent_lows  = lows[-lookback:]

    resistance_levels = []
    for i in range(2, len(recent_highs) - 2):
        if (recent_highs[i] > recent_highs[i - 1] and
                recent_highs[i] > recent_highs[i - 2] and
                recent_highs[i] > recent_highs[i + 1] and
                recent_highs[i] > recent_highs[i + 2]):
            resistance_levels.append(round(recent_highs[i], 5))

    support_levels = []
    for i in range(2, len(recent_lows) - 2):
        if (recent_lows[i] < recent_lows[i - 1] and
                recent_lows[i] < recent_lows[i - 2] and
                recent_lows[i] < recent_lows[i + 1] and
                recent_lows[i] < recent_lows[i + 2]):
            support_levels.append(round(recent_lows[i], 5))

    def deduplicate_levels(levels: list[float]) -> list[float]:
        if not levels:
            return []
        levels = sorted(set(levels))
        result = [levels[0]]
        for level in levels[1:]:
            if abs(level - result[-1]) / result[-1] > 0.0005:
                result.append(level)
        return result[-5:]

    return {
        "resistance": deduplicate_levels(resistance_levels),
        "support":    deduplicate_levels(support_levels),
        "pip_multiplier": pip_mult
    }


async def full_analysis(candle_data: dict) -> dict:
    """
    Run complete technical analysis on candle data.
    This is the main function called by the trading engine.

    Args:
        candle_data: Output from mt5_tool.get_candles()

    Returns:
        Complete analysis dict with all indicators and trading signals
    """
    if not candle_data.get("success") or not candle_data.get("candles"):
        return {"success": False, "error": "Invalid candle data"}

    candles   = candle_data["candles"]
    symbol    = candle_data.get("symbol",    "")
    timeframe = candle_data.get("timeframe", "")

    if len(candles) < 50:
        return {"success": False, "error": f"Not enough candles: {len(candles)} (need 50+)"}

    opens  = [c["open"]  for c in candles]
    highs  = [c["high"]  for c in candles]
    lows   = [c["low"]   for c in candles]
    closes = [c["close"] for c in candles]

    current_price = closes[-1]

    # ── Pip multiplier for this symbol ────────────────────────────────────────
    # CRITICAL: JPY pairs use 100, Gold uses 10, most others use 10000
    # Using wrong multiplier causes SL/TP of thousands of pips (the old bug)
    pip_mult = get_pip_multiplier(symbol)

    # ── Calculate all indicators ──────────────────────────────────────────────
    ema_20  = calculate_ema(closes, 20)
    ema_50  = calculate_ema(closes, 50)
    ema_200 = calculate_ema(closes, 200)
    rsi     = calculate_rsi(closes, 14)
    macd    = calculate_macd(closes)
    bb      = calculate_bollinger_bands(closes, 20)
    atr     = calculate_atr(highs, lows, closes, 14)
    sr      = find_support_resistance(highs, lows, closes, symbol)

    # ── Get latest values ─────────────────────────────────────────────────────
    latest_ema20     = ema_20[-1]  if ema_20  else None
    latest_ema50     = ema_50[-1]  if ema_50  else None
    latest_ema200    = ema_200[-1] if ema_200 else None
    latest_rsi       = rsi[-1]     if rsi     else None
    latest_macd      = macd["macd"][-1]      if macd["macd"]      else None
    latest_signal    = macd["signal"][-1]    if macd["signal"]    else None
    latest_hist      = macd["histogram"][-1] if macd["histogram"] else None
    prev_hist        = macd["histogram"][-2] if len(macd["histogram"]) > 1 else None
    latest_bb_upper  = bb["upper"][-1]  if bb["upper"]  else None
    latest_bb_middle = bb["middle"][-1] if bb["middle"] else None
    latest_bb_lower  = bb["lower"][-1]  if bb["lower"]  else None
    latest_atr       = atr[-1] if atr else None

    # ── Trend analysis ────────────────────────────────────────────────────────
    trend_signals = []
    bullish_count = 0
    bearish_count = 0

    if latest_ema200:
        if current_price > latest_ema200:
            trend_signals.append("Price ABOVE 200 EMA → long-term BULLISH")
            bullish_count += 2
        else:
            trend_signals.append("Price BELOW 200 EMA → long-term BEARISH")
            bearish_count += 2

    if latest_ema50:
        if current_price > latest_ema50:
            trend_signals.append("Price ABOVE 50 EMA → medium-term BULLISH")
            bullish_count += 1
        else:
            trend_signals.append("Price BELOW 50 EMA → medium-term BEARISH")
            bearish_count += 1

    if latest_ema20 and latest_ema50:
        if latest_ema20 > latest_ema50:
            trend_signals.append("EMA20 above EMA50 → short-term momentum BULLISH")
            bullish_count += 1
        else:
            trend_signals.append("EMA20 below EMA50 → short-term momentum BEARISH")
            bearish_count += 1

    # ── Momentum analysis ─────────────────────────────────────────────────────
    momentum_signals = []
    rsi_signal = "neutral"

    if latest_rsi is not None:
        if latest_rsi < 30:
            momentum_signals.append(f"RSI {latest_rsi} → OVERSOLD — potential BUY reversal")
            bullish_count += 2
            rsi_signal = "oversold"
        elif latest_rsi > 70:
            momentum_signals.append(f"RSI {latest_rsi} → OVERBOUGHT — potential SELL reversal")
            bearish_count += 2
            rsi_signal = "overbought"
        elif latest_rsi < 45:
            momentum_signals.append(f"RSI {latest_rsi} → bearish territory")
            bearish_count += 1
            rsi_signal = "bearish"
        elif latest_rsi > 55:
            momentum_signals.append(f"RSI {latest_rsi} → bullish territory")
            bullish_count += 1
            rsi_signal = "bullish"
        else:
            momentum_signals.append(f"RSI {latest_rsi} → neutral")

    if latest_hist is not None and prev_hist is not None:
        if latest_hist > 0 and prev_hist <= 0:
            momentum_signals.append("MACD histogram crossed ABOVE zero → bullish momentum")
            bullish_count += 2
        elif latest_hist < 0 and prev_hist >= 0:
            momentum_signals.append("MACD histogram crossed BELOW zero → bearish momentum")
            bearish_count += 2
        elif latest_hist > prev_hist:
            momentum_signals.append("MACD histogram increasing → strengthening bullish momentum")
            bullish_count += 1
        else:
            momentum_signals.append("MACD histogram decreasing → weakening / bearish momentum")
            bearish_count += 1

    # ── Bollinger Bands analysis ──────────────────────────────────────────────
    bb_signals = []
    if all(v is not None for v in [latest_bb_upper, latest_bb_lower, latest_bb_middle]):
        bb_range = latest_bb_upper - latest_bb_lower  # type: ignore[operator]
        if current_price <= latest_bb_lower:  # type: ignore[operator]
            bb_signals.append("Price at LOWER Bollinger Band → oversold, potential bounce UP")
            bullish_count += 1
        elif current_price >= latest_bb_upper:  # type: ignore[operator]
            bb_signals.append("Price at UPPER Bollinger Band → overbought, potential reversal DOWN")
            bearish_count += 1
        else:
            bb_position = round(
                (current_price - latest_bb_lower) / bb_range * 100, 1  # type: ignore[operator]
            ) if bb_range > 0 else 50
            bb_signals.append(f"Price at {bb_position}% of Bollinger Band range")

    # ── Support & Resistance ──────────────────────────────────────────────────
    # Use symbol-aware pip_mult so distances display correctly for all pairs
    sr_signals         = []
    nearest_support    = None
    nearest_resistance = None

    if sr["support"]:
        above_support = [s for s in sr["support"] if s < current_price]
        if above_support:
            nearest_support = max(above_support)
            distance_pips   = round((current_price - nearest_support) * pip_mult, 1)
            sr_signals.append(f"Nearest support: {nearest_support} ({distance_pips} pips away)")

    if sr["resistance"]:
        below_resistance = [r for r in sr["resistance"] if r > current_price]
        if below_resistance:
            nearest_resistance = min(below_resistance)
            distance_pips      = round((nearest_resistance - current_price) * pip_mult, 1)
            sr_signals.append(f"Nearest resistance: {nearest_resistance} ({distance_pips} pips away)")

    # ── Overall signal ────────────────────────────────────────────────────────
    total_signals = bullish_count + bearish_count
    bull_pct = round(bullish_count / total_signals * 100, 1) if total_signals > 0 else 50

    if bull_pct >= 70:
        overall_signal = "STRONG BUY"
        confidence     = bull_pct
    elif bull_pct >= 60:
        overall_signal = "BUY"
        confidence     = bull_pct
    elif bull_pct <= 30:
        overall_signal = "STRONG SELL"
        confidence     = round(100 - bull_pct, 1)
    elif bull_pct <= 40:
        overall_signal = "SELL"
        confidence     = round(100 - bull_pct, 1)
    else:
        overall_signal = "NEUTRAL — WAIT"
        confidence     = 50

    # ── ATR-based pip suggestions ─────────────────────────────────────────────
    # Use pip_mult so JPY pairs get ~20-30 pip SL not ~3000 pip SL
    suggested_sl_pips = None
    suggested_tp_pips = None
    atr_pips          = None

    if latest_atr is not None:
        atr_pips          = round(latest_atr * pip_mult, 1)
        suggested_sl_pips = round(atr_pips * 1.5, 1)   # SL = 1.5x ATR
        suggested_tp_pips = round(atr_pips * 2.0, 1)   # TP = 2.0x ATR (1:1.33 RR)

    return {
        "success":   True,
        "symbol":    symbol,
        "timeframe": timeframe,
        "current_price": current_price,
        "pip_multiplier": pip_mult,

        # Individual indicators
        "ema_20":  round(latest_ema20,  5) if latest_ema20  else None,
        "ema_50":  round(latest_ema50,  5) if latest_ema50  else None,
        "ema_200": round(latest_ema200, 5) if latest_ema200 else None,
        "rsi":        latest_rsi,
        "rsi_signal": rsi_signal,
        "macd_line":      round(latest_macd,   6) if latest_macd   else None,
        "macd_signal":    round(latest_signal, 6) if latest_signal else None,
        "macd_histogram": round(latest_hist,   6) if latest_hist   else None,
        "bb_upper":  latest_bb_upper,
        "bb_middle": latest_bb_middle,
        "bb_lower":  latest_bb_lower,
        "atr":      round(latest_atr, 6) if latest_atr else None,
        "atr_pips": atr_pips,

        # Support & Resistance
        "nearest_support":    nearest_support,
        "nearest_resistance": nearest_resistance,
        "all_support":        sr["support"],
        "all_resistance":     sr["resistance"],

        # Signal breakdown
        "trend_signals":    trend_signals,
        "momentum_signals": momentum_signals,
        "bb_signals":       bb_signals,
        "sr_signals":       sr_signals,

        # Summary
        "bullish_score":   bullish_count,
        "bearish_score":   bearish_count,
        "bullish_percent": bull_pct,
        "overall_signal":  overall_signal,
        "confidence_percent": confidence,

        # Trade suggestions (now correctly calculated per symbol type)
        "suggested_sl_pips": suggested_sl_pips,
        "suggested_tp_pips": suggested_tp_pips,
    }