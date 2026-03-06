# backend/agents/trading_engine.py
"""
AI Trading Engine for OpenClaw.
Uses Claude + MT5 + Technical Analysis + News Sentiment
to make autonomous trading decisions on Deriv MT5.

Flow:
  1. Check account + open positions
  2. Fetch news ONCE for the whole run
  3. Get live price + candles for each symbol
  4. Run full technical analysis per symbol
  5. Pick the highest confidence setup
  6. Claude makes final BUY / SELL / WAIT decision
  7. Execute trade if confidence >= threshold
  8. Log everything to dashboard in real time
"""
from typing import Optional
from anthropic import Anthropic
from anthropic.types import TextBlock
from backend.config import settings
from backend.db.models import Agent as AgentModel, AgentEvent, AgentStatus
from backend.services.redis_service import publish_event
from backend.agents.tools.mt5_tool import (
    get_live_price, get_candles, get_account_info,
    get_open_positions, place_trade, get_trade_history,
    ALL_SYMBOLS
)
from backend.agents.tools.ta_tool import full_analysis
from backend.agents.tools.news_tool import get_forex_news
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import json
import re

client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

# ── Trading config ─────────────────────────────────────────────────────────────
MIN_CONFIDENCE      = 70
MAX_OPEN_TRADES     = 3
ANALYSIS_TIMEFRAMES = ["H1", "H4"]
CANDLES_TO_FETCH    = 200


async def log_event(
    db: AsyncSession,
    agent: AgentModel,
    event_type: str,
    message: str,
    value: Optional[float] = None
):
    """Log trading event to database and stream to dashboard."""
    event = AgentEvent(
        agent_id=agent.id,
        event_type=event_type,
        message=message,
        value=value
    )
    db.add(event)
    await db.flush()

    await publish_event(str(agent.user_id), {  # type: ignore[arg-type]
        "agent_id":   agent.id,
        "agent_name": agent.name,
        "type":       event_type,
        "message":    message,
        "value":      value
    })


async def run_trading_agent(agent_record: AgentModel, db: AsyncSession):
    """Main trading agent execution — called by Celery worker."""
    agent_record.status      = AgentStatus.RUNNING   # type: ignore[assignment]
    agent_record.last_active = datetime.utcnow()      # type: ignore[assignment]
    await db.commit()

    desires: dict      = dict(agent_record.desires) if agent_record.desires else {}  # type: ignore[arg-type]
    memory_list: list  = list(agent_record.memory)  if agent_record.memory  else []  # type: ignore[arg-type]
    recent_memory      = memory_list[-10:]

    stake_level = desires.get("stake_level", "conservative")
    stake_map   = {
        "conservative": 0.01,
        "moderate":     0.05,
        "aggressive":   0.10,
    }
    lot_size = stake_map.get(stake_level, 0.01)

    await log_event(db, agent_record, "start",
        f"{agent_record.name} scanning markets. Stake: {stake_level} ({lot_size} lots)")

    try:
        # ── Step 1: Account check ──────────────────────────────────────────────
        account = await get_account_info()
        if not account["success"]:
            await log_event(db, agent_record, "error",
                f"MT5 connection failed: {account['error']}")
            agent_record.status = AgentStatus.ERROR  # type: ignore[assignment]
            await db.commit()
            return

        await log_event(db, agent_record, "portal",
            f"Account: Balance ${account['balance']} | Equity ${account['equity']} | Free Margin ${account['free_margin']}")

        # ── Step 2: Check open position count ─────────────────────────────────
        open_positions = await get_open_positions()
        if open_positions["success"] and open_positions["total"] >= MAX_OPEN_TRADES:
            await log_event(db, agent_record, "portal",
                f"Max open trades reached ({MAX_OPEN_TRADES}). Monitoring existing positions.")
            agent_record.status = AgentStatus.IDLE  # type: ignore[assignment]
            await db.commit()
            return

        # ── Step 3: Fetch news ONCE for the entire run ────────────────────────
        # One SerpAPI call covers all 17 symbols — saves credits
        await log_event(db, agent_record, "scan",
            f"Fetching market news and sentiment...")
        shared_news = await get_forex_news("")  # empty = general market news

        if not shared_news.get("safe_to_trade", True):
            await log_event(db, agent_record, "portal",
                f"⚠ {shared_news.get('reason', 'High impact news detected')} — standing down")
            agent_record.status = AgentStatus.IDLE  # type: ignore[assignment]
            await db.commit()
            return

        await log_event(db, agent_record, "portal",
            f"News: {shared_news.get('sentiment', 'neutral').upper()} sentiment ({shared_news.get('sentiment_score', 50)}% bullish) | {shared_news.get('reason', '')}")

        # ── Step 4: Scan all symbols ───────────────────────────────────────────
        await log_event(db, agent_record, "scan",
            f"Scanning {len(ALL_SYMBOLS)} symbols for high-confidence setups...")

        best_setup   = None
        best_confidence = 0

        for symbol in ALL_SYMBOLS:
            try:
                setup = await analyze_symbol(symbol, shared_news)
                if setup is None:
                    continue
                signal = setup.get("signal", "")
                if "WAIT" in signal or "NEUTRAL" in signal:
                    continue
                if setup.get("confidence", 0) > best_confidence:
                    best_confidence = setup["confidence"]
                    best_setup      = setup
            except Exception:
                continue

        if not best_setup:
            await log_event(db, agent_record, "wait",
                "No high-confidence setups found this cycle. Markets ranging — waiting.")
            agent_record.status = AgentStatus.IDLE  # type: ignore[assignment]
            await db.commit()
            return

        await log_event(db, agent_record, "portal",
            f"Best setup: {best_setup['symbol']} | Signal: {best_setup['signal']} | Confidence: {best_setup['confidence']}%")

        # ── Step 5: Claude makes final decision ────────────────────────────────
        decision = await claude_trading_decision(
            agent_record   = agent_record,
            setup          = best_setup,
            account        = account,
            open_positions = open_positions,
            recent_memory  = recent_memory,
            lot_size       = lot_size,
            news           = shared_news
        )

        await log_event(db, agent_record, "portal",
            f"Claude: {decision.get('action', 'WAIT')} | {decision.get('reason', '')[:200]}")

        # ── Step 6: Execute trade ──────────────────────────────────────────────
        if decision.get("action") in ("BUY", "SELL") and decision.get("confidence", 0) >= MIN_CONFIDENCE:
            symbol    = best_setup["symbol"]
            direction = decision["action"]
            sl_pips   = decision.get("sl_pips",  best_setup.get("suggested_sl_pips", 30))
            tp_pips   = decision.get("tp_pips",  best_setup.get("suggested_tp_pips", 50))

            await log_event(db, agent_record, "trade",
                f"Placing {direction} on {symbol} | Lot: {lot_size} | SL: {sl_pips} pips | TP: {tp_pips} pips")

            trade_result = await place_trade(
                symbol           = symbol,
                direction        = direction,
                volume           = lot_size,
                stop_loss_pips   = sl_pips,
                take_profit_pips = tp_pips,
                comment          = f"OpenClaw-{agent_record.name[:10]}"
            )

            if trade_result["success"]:
                await log_event(db, agent_record, "trade",
                    f"✅ TRADE PLACED: {direction} {symbol} at {trade_result['entry_price']} | Ticket #{trade_result['ticket']}",
                    value=0.0
                )
            else:
                await log_event(db, agent_record, "error",
                    f"Trade failed: {trade_result['error']}")
        else:
            await log_event(db, agent_record, "wait",
                f"WAITING — confidence {decision.get('confidence', 0)}% below threshold {MIN_CONFIDENCE}%")

        # ── Step 7: Daily P&L report ───────────────────────────────────────────
        history = await get_trade_history(days=1)
        if history["success"] and history["summary"].get("total_trades", 0) > 0:
            summary      = history["summary"]
            daily_profit = summary.get("total_profit", 0)
            win_rate     = summary.get("win_rate_percent", 0)
            total_trades = summary.get("total_trades", 0)

            agent_record.total_value_generated = (  # type: ignore[assignment]
                (agent_record.total_value_generated or 0) + max(daily_profit, 0)
            )
            await log_event(db, agent_record, "pnl",
                f"Daily P&L: ${daily_profit} | Win rate: {win_rate}% | Trades: {total_trades}",
                value=daily_profit
            )

        # ── Step 8: Update memory ──────────────────────────────────────────────
        memory_update = decision.get("memory_update", "")
        if memory_update:
            memory_list.append(memory_update)
            agent_record.memory = memory_list[-20:]  # type: ignore[assignment]

        agent_record.task_count = (agent_record.task_count or 0) + 1  # type: ignore[assignment]
        agent_record.status     = AgentStatus.IDLE                      # type: ignore[assignment]
        await db.commit()

    except Exception as e:
        agent_record.status = AgentStatus.ERROR  # type: ignore[assignment]
        await log_event(db, agent_record, "error", f"Trading agent error: {str(e)}")
        await db.commit()


async def analyze_symbol(symbol: str, shared_news: dict) -> Optional[dict]:
    """Run full technical analysis on one symbol using pre-fetched news."""
    try:
        analyses: dict = {}
        for tf in ANALYSIS_TIMEFRAMES:
            candles = await get_candles(symbol, tf, CANDLES_TO_FETCH)
            if candles["success"]:
                ta = await full_analysis(candles)
                if ta["success"]:
                    analyses[tf] = ta

        if not analyses:
            return None

        primary = analyses.get("H1") or list(analyses.values())[0]
        htf     = analyses.get("H4")

        price_data = await get_live_price(symbol)
        if not price_data["success"]:
            return None

        # Confidence calculation with H4 confluence
        confidence = primary["confidence_percent"]

        if htf:
            h1_bull = "BUY"  in primary["overall_signal"]
            h4_bull = "BUY"  in htf["overall_signal"]
            h1_bear = "SELL" in primary["overall_signal"]
            h4_bear = "SELL" in htf["overall_signal"]

            if (h1_bull and h4_bull) or (h1_bear and h4_bear):
                confidence = min(confidence + 10, 95)   # confluence bonus
            elif (h1_bull and h4_bear) or (h1_bear and h4_bull):
                confidence = max(confidence - 15, 0)    # conflicting signals

        # Apply news sentiment modifier
        sentiment = shared_news.get("sentiment", "neutral")
        if "BUY"  in primary["overall_signal"] and sentiment == "bearish":
            confidence = max(confidence - 10, 0)
        elif "SELL" in primary["overall_signal"] and sentiment == "bullish":
            confidence = max(confidence - 10, 0)

        return {
            "symbol":             symbol,
            "current_price":      price_data["ask"],
            "bid":                price_data["bid"],
            "ask":                price_data["ask"],
            "spread_pips":        price_data["spread_pips"],
            "signal":             primary["overall_signal"],
            "confidence":         round(confidence, 1),
            "rsi":                primary["rsi"],
            "rsi_signal":         primary["rsi_signal"],
            "macd_histogram":     primary["macd_histogram"],
            "ema_20":             primary["ema_20"],
            "ema_50":             primary["ema_50"],
            "ema_200":            primary["ema_200"],
            "bb_upper":           primary["bb_upper"],
            "bb_lower":           primary["bb_lower"],
            "nearest_support":    primary["nearest_support"],
            "nearest_resistance": primary["nearest_resistance"],
            "trend_signals":      primary["trend_signals"],
            "momentum_signals":   primary["momentum_signals"],
            "h4_signal":          htf["overall_signal"] if htf else "N/A",
            "h4_confidence":      htf["confidence_percent"] if htf else None,
            "news_safe":          shared_news.get("safe_to_trade", True),
            "news_reason":        shared_news.get("reason", ""),
            "sentiment":          sentiment,
            "sentiment_score":    shared_news.get("sentiment_score", 50),
            "suggested_sl_pips":  primary["suggested_sl_pips"],
            "suggested_tp_pips":  primary["suggested_tp_pips"],
            "atr_pips":           primary["atr_pips"],
        }

    except Exception:
        return None


async def claude_trading_decision(
    agent_record:   AgentModel,
    setup:          dict,
    account:        dict,
    open_positions: dict,
    recent_memory:  list,
    lot_size:       float,
    news:           dict
) -> dict:
    """Ask Claude to make the final trading decision."""
    desires: dict = dict(agent_record.desires) if agent_record.desires else {}  # type: ignore[arg-type]

    system_prompt = f"""You are {agent_record.name}, an expert forex and commodities trader on Deriv MT5.

Role: {agent_record.role}
Goal: {agent_record.goal}

TRADING RULES:
1. Only trade when confidence is genuinely 70%+
2. Never trade against the H4 trend without very strong H1 reversal evidence
3. Always use the ATR-based SL and TP from the analysis
4. If in doubt — WAIT. Capital preservation is priority.
5. Maximum {MAX_OPEN_TRADES} concurrent trades

Respond with a valid JSON object ONLY. No other text."""

    user_prompt = f"""
ACCOUNT:
Balance: ${account['balance']} | Equity: ${account['equity']} | Free Margin: ${account['free_margin']}
Open positions: {open_positions['total']} / {MAX_OPEN_TRADES}

BEST SETUP: {setup['symbol']}
Price: {setup['current_price']} | Spread: {setup['spread_pips']} pips

TECHNICAL ANALYSIS:
H1 Signal: {setup['signal']} ({setup['confidence']}% confidence)
H4 Signal: {setup['h4_signal']}
RSI: {setup['rsi']} → {setup['rsi_signal']}
MACD Histogram: {setup['macd_histogram']}
EMA 20/50/200: {setup['ema_20']} / {setup['ema_50']} / {setup['ema_200']}
BB Upper/Lower: {setup['bb_upper']} / {setup['bb_lower']}
Support: {setup['nearest_support']} | Resistance: {setup['nearest_resistance']}
Trend: {setup['trend_signals']}
Momentum: {setup['momentum_signals']}
Suggested SL: {setup['suggested_sl_pips']} pips | TP: {setup['suggested_tp_pips']} pips

NEWS & SENTIMENT:
Safe to trade: {setup['news_safe']}
Sentiment: {setup['sentiment']} ({setup['sentiment_score']}% bullish)
Headlines: {[h['title'] for h in news.get('news_headlines', [])[:3]]}

MEMORY:
{json.dumps(recent_memory, indent=2)}

LOT SIZE: {lot_size}

Respond ONLY with this JSON:
{{
  "action": "BUY" or "SELL" or "WAIT",
  "symbol": "{setup['symbol']}",
  "confidence": 0-100,
  "sl_pips": stop loss in pips,
  "tp_pips": take profit in pips,
  "reason": "detailed explanation",
  "memory_update": "lesson to remember for next time",
  "risk_assessment": "low/medium/high"
}}"""

    try:
        response = client.messages.create(
            model      = "claude-sonnet-4-6",
            max_tokens = 1024,
            system     = system_prompt,
            messages   = [{"role": "user", "content": user_prompt}]
        )

        result_text = ""
        for block in response.content:
            if isinstance(block, TextBlock):
                result_text = block.text
                break

        clean      = re.sub(r"```(?:json)?|```", "", result_text).strip()
        json_match = re.search(r'\{.*\}', clean, re.DOTALL)

        if json_match:
            return json.loads(json_match.group())
        else:
            return {"action": "WAIT", "confidence": 0,
                    "reason": "Could not parse Claude response", "memory_update": ""}

    except Exception as e:
        return {"action": "WAIT", "confidence": 0,
                "reason": f"Claude error: {str(e)}", "memory_update": ""}