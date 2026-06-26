# Step 6: Config/settings
# backend/config.py
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from pathlib import Path

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    ANTHROPIC_API_KEY: str
    STRIPE_SECRET_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None
    PAYSTACK_SECRET_KEY: str | None = None
    PAYSTACK_PUBLIC_KEY: str | None = None
    JWT_SECRET: str
    ADMIN_SECRET_KEY: str = "Ray_Charles_Wanjie_090409"
    FRONTEND_URL: str = "http://localhost:3000"

    # ── Agent Tools ────────────────────────────────────────────────────────────
    SERPAPI_KEY: str = ""
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "onboarding@resend.dev"
    SCRAPER_API_KEY: str = ""

    # ── Deriv MT5 Trading ──────────────────────────────────────────────────────
    MT5_LOGIN: str = ""          # your MT5 login number e.g. 6030498
    MT5_PASSWORD: str = ""       # your MT5 password
    MT5_SERVER: str = "DerivSVG-Server"  # Deriv-Demo for demo, Deriv-Server for live

    # Dynamically locate .env in backend/ or project root
    model_config = ConfigDict(
        env_file=str(Path(__file__).parent / ".env") if (Path(__file__).parent / ".env").exists() else str(Path(__file__).parent.parent / ".env"),  # type: ignore
        case_sensitive=False
    )

settings = Settings()  # type: ignore[call-arg]