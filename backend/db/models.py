"""Database models for OpenClaw."""
import uuid
import enum
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


def gen_id():
    """Generate a UUID string for primary keys."""
    return str(uuid.uuid4())


class SubscriptionTier(enum.Enum):
    """User subscription tiers."""
    FREE = "free"
    STARTER = "starter"
    EMPIRE = "empire"
    UNLIMITED = "unlimited"
    ADMIN = "admin"


class AgentStatus(enum.Enum):
    """Agent execution status."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    COMPLETED = "completed"


class AgentType(enum.Enum):
    """Agent type — determines which engine handles execution."""
    STANDARD = "standard"   # Uses engine.py — web search, email, SEO, Upwork, LinkedIn
    TRADING  = "trading"    # Uses trading_engine.py — Deriv MT5 forex/commodities


class User(Base):
    """User model for authentication and subscription management."""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_id)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    is_admin = Column(Boolean, default=False)
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    agent_limit = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    agents = relationship("Agent", back_populates="owner", cascade="all, delete-orphan")


class Agent(Base):
    """Agent model for autonomous AI agents."""
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    goal = Column(String, nullable=False)
    backstory = Column(String, nullable=False)
    status = Column(Enum(AgentStatus), default=AgentStatus.IDLE)

    # ── Agent type — routes to correct engine ─────────────────────────────────
    agent_type = Column(Enum(AgentType), default=AgentType.STANDARD, nullable=False)

    # ── Standard agent fields ──────────────────────────────────────────────────
    desires = Column(JSON, default={})   # greed, autonomy, expansion, curiosity + stake_level
    memory  = Column(JSON, default=[])   # rolling memory of past actions/lessons

    # ── Trading agent fields ───────────────────────────────────────────────────
    # trading_pairs: list of symbols to trade e.g. ["EURUSD", "XAUUSD"]
    trading_pairs = Column(JSON, default=[])
    # stake_level: "conservative" | "moderate" | "aggressive"
    stake_level = Column(String, default="conservative", nullable=False)

    # ── Shared stats ───────────────────────────────────────────────────────────
    total_value_generated = Column(Float, default=0.0)
    task_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    last_active = Column(DateTime, nullable=True)

    owner  = relationship("User", back_populates="agents")
    events = relationship("AgentEvent", back_populates="agent", cascade="all, delete-orphan")


class AgentEvent(Base):
    """Agent event log model."""
    __tablename__ = "agent_events"

    id = Column(String, primary_key=True, default=gen_id)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    event_type = Column(String, nullable=False)
    message = Column(String, nullable=False)
    value = Column(Float, nullable=True)
    meta_data = Column(JSON, default={})
    created_at = Column(DateTime, server_default=func.now())

    agent = relationship("Agent", back_populates="events")