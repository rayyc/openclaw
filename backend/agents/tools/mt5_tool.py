# backend/agents/tools/mt5_tool.py
"""
Deriv MT5 trading tool.
Connects to Deriv-Demo MT5 server for price data and trade execution.
Uses MetaTrader5 Python library — Windows only (perfect for local dev).
"""
# MetaTrader5 has no type stubs — import as a plain module reference
# and access all attributes via getattr to avoid Pylance attribute errors
import importlib
import datetime as dt
from datetime import datetime, timezone
from backend.config import settings
from typing import Any

# Load MT5 at runtime — all calls go through _mt5 to avoid Pylance complaints
_mt5: Any = importlib.import_module("MetaTrader5")

# ── Deriv MT5 connection config ───────────────────────────────────────────────
MT5_LOGIN    = settings.MT5_LOGIN
MT5_PASSWORD = settings.MT5_PASSWORD
MT5_SERVER   = settings.MT5_SERVER  # "Deriv-Demo"

# ── Supported instruments ─────────────────────────────────────────────────────
FOREX_PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF",
    "AUDUSD", "USDCAD", "NZDUSD",
    "EURGBP", "EURJPY", "GBPJPY",
    "EURCAD", "GBPCAD", "AUDCAD",
]

COMMODITIES = [
    "XAUUSD",   # Gold
    "XAGUSD",   # Silver
    "USOIL",    # WTI Crude Oil
    "UKOIL",    # Brent Crude
]

ALL_SYMBOLS = FOREX_PAIRS + COMMODITIES

# ── Timeframe constants (accessed via _mt5 to avoid attribute errors) ─────────
def _tf(name: str) -> Any:
    return getattr(_mt5, name)

TIMEFRAMES: dict[str, Any] = {
    "M1":  _tf("TIMEFRAME_M1"),
    "M5":  _tf("TIMEFRAME_M5"),
    "M15": _tf("TIMEFRAME_M15"),
    "M30": _tf("TIMEFRAME_M30"),
    "H1":  _tf("TIMEFRAME_H1"),
    "H4":  _tf("TIMEFRAME_H4"),
    "D1":  _tf("TIMEFRAME_D1"),
}


# ── Connection helpers ────────────────────────────────────────────────────────

def connect() -> bool:
    """Initialize and connect to Deriv MT5."""
    if not _mt5.initialize():
        return False
    authorized = _mt5.login(
        login=int(MT5_LOGIN),
        password=MT5_PASSWORD,
        server=MT5_SERVER
    )
    return bool(authorized)


def disconnect() -> None:
    """Shutdown MT5 connection."""
    _mt5.shutdown()


# ── Price data ────────────────────────────────────────────────────────────────

async def get_live_price(symbol: str) -> dict:
    """Get current bid/ask price for a symbol."""
    try:
        if not connect():
            return {"success": False, "error": "MT5 connection failed"}

        tick = _mt5.symbol_info_tick(symbol)
        if tick is None:
            disconnect()
            return {"success": False, "error": f"Symbol {symbol} not found or market closed"}

        info   = _mt5.symbol_info(symbol)
        digits = info.digits if info else 5
        spread_pips = round((tick.ask - tick.bid) * (10 ** digits), 1)

        disconnect()
        return {
            "success":     True,
            "symbol":      symbol,
            "bid":         round(tick.bid, digits),
            "ask":         round(tick.ask, digits),
            "spread_pips": spread_pips,
            "time":        datetime.fromtimestamp(tick.time, tz=timezone.utc).isoformat()
        }

    except Exception as e:
        disconnect()
        return {"success": False, "error": f"get_live_price error: {str(e)}"}


async def get_candles(symbol: str, timeframe: str = "H1", count: int = 100) -> dict:
    """Get historical candle data for technical analysis."""
    try:
        if not connect():
            return {"success": False, "error": "MT5 connection failed"}

        tf    = TIMEFRAMES.get(timeframe, _tf("TIMEFRAME_H1"))
        count = min(count, 500)

        rates = _mt5.copy_rates_from_pos(symbol, tf, 0, count)
        if rates is None or len(rates) == 0:
            disconnect()
            return {"success": False, "error": f"No candle data for {symbol}"}

        candles = []
        for r in rates:
            candles.append({
                "time":   datetime.fromtimestamp(r["time"], tz=timezone.utc).isoformat(),
                "open":   round(float(r["open"]),  5),
                "high":   round(float(r["high"]),  5),
                "low":    round(float(r["low"]),   5),
                "close":  round(float(r["close"]), 5),
                "volume": int(r["tick_volume"])
            })

        disconnect()
        return {
            "success":   True,
            "symbol":    symbol,
            "timeframe": timeframe,
            "count":     len(candles),
            "candles":   candles
        }

    except Exception as e:
        disconnect()
        return {"success": False, "error": f"get_candles error: {str(e)}"}


async def get_account_info() -> dict:
    """Get current MT5 account balance, equity, and margin info."""
    try:
        if not connect():
            return {"success": False, "error": "MT5 connection failed"}

        info = _mt5.account_info()
        if info is None:
            disconnect()
            return {"success": False, "error": "Could not retrieve account info"}

        disconnect()
        return {
            "success":      True,
            "login":        info.login,
            "server":       info.server,
            "balance":      round(info.balance,      2),
            "equity":       round(info.equity,       2),
            "margin":       round(info.margin,       2),
            "free_margin":  round(info.margin_free,  2),
            "margin_level": round(info.margin_level, 2),
            "currency":     info.currency,
            "leverage":     info.leverage
        }

    except Exception as e:
        disconnect()
        return {"success": False, "error": f"get_account_info error: {str(e)}"}


async def get_open_positions() -> dict:
    """Get all currently open positions."""
    try:
        if not connect():
            return {"success": False, "error": "MT5 connection failed"}

        positions = _mt5.positions_get()
        if positions is None:
            disconnect()
            return {"success": True, "positions": [], "total": 0}

        result = []
        for p in positions:
            result.append({
                "ticket":        p.ticket,
                "symbol":        p.symbol,
                "type":          "BUY" if p.type == _tf("ORDER_TYPE_BUY") else "SELL",
                "volume":        p.volume,
                "open_price":    round(p.price_open,    5),
                "current_price": round(p.price_current, 5),
                "sl":            round(p.sl, 5),
                "tp":            round(p.tp, 5),
                "profit":        round(p.profit, 2),
                "open_time":     datetime.fromtimestamp(p.time, tz=timezone.utc).isoformat(),
                "comment":       p.comment
            })

        disconnect()
        return {
            "success":      True,
            "positions":    result,
            "total":        len(result),
            "total_profit": round(sum(p["profit"] for p in result), 2)
        }

    except Exception as e:
        disconnect()
        return {"success": False, "error": f"get_open_positions error: {str(e)}"}


# ── Trade execution ───────────────────────────────────────────────────────────

async def place_trade(
    symbol: str,
    direction: str,
    volume: float,
    stop_loss_pips: float,
    take_profit_pips: float,
    comment: str = "OpenClaw Agent"
) -> dict:
    """Place a market order on Deriv MT5."""
    try:
        if not connect():
            return {"success": False, "error": "MT5 connection failed"}

        info = _mt5.symbol_info(symbol)
        if info is None:
            disconnect()
            return {"success": False, "error": f"Symbol {symbol} not available"}

        tick = _mt5.symbol_info_tick(symbol)
        if tick is None:
            disconnect()
            return {"success": False, "error": f"Could not get price for {symbol}"}

        digits   = info.digits
        pip_size = 0.0001 if digits in (4, 5) else 0.01

        if direction.upper() == "BUY":
            order_type = _tf("ORDER_TYPE_BUY")
            price = tick.ask
            sl = round(price - (stop_loss_pips   * pip_size), digits)
            tp = round(price + (take_profit_pips * pip_size), digits)
        elif direction.upper() == "SELL":
            order_type = _tf("ORDER_TYPE_SELL")
            price = tick.bid
            sl = round(price + (stop_loss_pips   * pip_size), digits)
            tp = round(price - (take_profit_pips * pip_size), digits)
        else:
            disconnect()
            return {"success": False, "error": f"Invalid direction: {direction}. Use BUY or SELL"}

        request = {
            "action":       _tf("TRADE_ACTION_DEAL"),
            "symbol":       symbol,
            "volume":       float(volume),
            "type":         order_type,
            "price":        price,
            "sl":           sl,
            "tp":           tp,
            "deviation":    10,
            "magic":        20250228,
            "comment":      comment[:31],
            "type_time":    _tf("ORDER_TIME_GTC"),
            "type_filling": _tf("ORDER_FILLING_IOC"),
        }

        result = _mt5.order_send(request)

        if result is None:
            error = _mt5.last_error()
            disconnect()
            return {"success": False, "error": f"Order send failed: {error}"}

        if result.retcode != _tf("TRADE_RETCODE_DONE"):
            disconnect()
            return {
                "success": False,
                "error":   f"Trade rejected: {result.comment} (code {result.retcode})"
            }

        disconnect()
        return {
            "success":     True,
            "ticket":      result.order,
            "symbol":      symbol,
            "direction":   direction.upper(),
            "volume":      volume,
            "entry_price": round(result.price, digits),
            "stop_loss":   sl,
            "take_profit": tp,
            "comment":     comment
        }

    except Exception as e:
        disconnect()
        return {"success": False, "error": f"place_trade error: {str(e)}"}


async def close_trade(ticket: int) -> dict:
    """Close a specific open position by ticket number."""
    try:
        if not connect():
            return {"success": False, "error": "MT5 connection failed"}

        position = _mt5.positions_get(ticket=ticket)
        if not position:
            disconnect()
            return {"success": False, "error": f"Position {ticket} not found"}

        pos       = position[0]
        symbol    = pos.symbol
        volume    = pos.volume
        direction = pos.type

        tick = _mt5.symbol_info_tick(symbol)
        if tick is None:
            disconnect()
            return {"success": False, "error": f"Could not get price for {symbol}"}

        if direction == _tf("ORDER_TYPE_BUY"):
            close_type = _tf("ORDER_TYPE_SELL")
            price = tick.bid
        else:
            close_type = _tf("ORDER_TYPE_BUY")
            price = tick.ask

        request = {
            "action":       _tf("TRADE_ACTION_DEAL"),
            "symbol":       symbol,
            "volume":       volume,
            "type":         close_type,
            "position":     ticket,
            "price":        price,
            "deviation":    10,
            "magic":        20250228,
            "comment":      "OpenClaw Close",
            "type_time":    _tf("ORDER_TIME_GTC"),
            "type_filling": _tf("ORDER_FILLING_IOC"),
        }

        result = _mt5.order_send(request)

        if result is None or result.retcode != _tf("TRADE_RETCODE_DONE"):
            error = _mt5.last_error() if result is None else result.comment
            disconnect()
            return {"success": False, "error": f"Close failed: {error}"}

        disconnect()
        return {
            "success":     True,
            "ticket":      ticket,
            "symbol":      symbol,
            "close_price": round(price, 5),
            "profit":      round(pos.profit, 2)
        }

    except Exception as e:
        disconnect()
        return {"success": False, "error": f"close_trade error: {str(e)}"}


async def get_trade_history(days: int = 7) -> dict:
    """Get closed trade history for the last N days."""
    try:
        if not connect():
            return {"success": False, "error": "MT5 connection failed"}

        now       = datetime.now(tz=timezone.utc)
        from_date = now - dt.timedelta(days=days)

        deals = _mt5.history_deals_get(from_date, now)
        if deals is None:
            disconnect()
            return {"success": True, "trades": [], "summary": {}}

        trades: list[dict] = []
        total_profit = 0.0
        wins   = 0
        losses = 0

        for d in deals:
            if d.type not in (_tf("DEAL_TYPE_BUY"), _tf("DEAL_TYPE_SELL")):
                continue
            profit = round(d.profit, 2)
            total_profit += profit
            if profit > 0:
                wins += 1
            elif profit < 0:
                losses += 1

            trades.append({
                "ticket":  d.order,
                "symbol":  d.symbol,
                "type":    "BUY" if d.type == _tf("DEAL_TYPE_BUY") else "SELL",
                "volume":  d.volume,
                "price":   round(d.price, 5),
                "profit":  profit,
                "time":    datetime.fromtimestamp(d.time, tz=timezone.utc).isoformat(),
                "comment": d.comment
            })

        total_trades = wins + losses
        win_rate = round((wins / total_trades * 100), 1) if total_trades > 0 else 0

        disconnect()
        return {
            "success": True,
            "trades":  trades,
            "summary": {
                "total_trades":     total_trades,
                "wins":             wins,
                "losses":           losses,
                "win_rate_percent": win_rate,
                "total_profit":     round(total_profit, 2),
                "period_days":      days
            }
        }

    except Exception as e:
        disconnect()
        return {"success": False, "error": f"get_trade_history error: {str(e)}"}