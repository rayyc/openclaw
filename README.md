# OpenClaw

Autonomous AI agent platform with subscription-based billing. Deploy AI agents that use real-world tools or trade forex and commodities on Deriv MT5.

## What It Does

**Standard Agents** — Claude-powered agents that autonomously use real-world tools to complete goals:
- Google Search (SerpAPI)
- Web Scraping (ScraperAPI + BeautifulSoup)
- Email outreach (Resend)
- SEO research
- Upwork job finding
- LinkedIn lead generation

**Trading Agents** — Claude-powered agents that trade forex and commodities on Deriv MT5:
- Connects to Deriv MT5 (demo or real account)
- Scans 17 forex pairs and commodities
- Runs 5-layer technical analysis (EMA, RSI, MACD, Bollinger Bands, ATR)
- Checks news sentiment before every trade
- Claude makes final BUY/SELL/WAIT decision
- Executes trades with automatic Stop Loss and Take Profit
- Builds trading memory — learns from wins and losses over time

## Tech Stack

### Backend
- **Framework**: FastAPI + AsyncIO
- **Database**: PostgreSQL + SQLAlchemy (async)
- **Task Queue**: Celery + Redis
- **AI**: Anthropic Claude API (claude-sonnet-4-6)
- **Trading**: MetaTrader5 Python library (Deriv MT5)
- **Payments**: Paystack API
- **Server**: Uvicorn

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **UI**: React 18 + Tailwind CSS
- **State**: Zustand
- **Real-time**: WebSocket

## Project Structure

```
openclaw/
├── backend/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── agents.py        # Agent deploy/run/delete (standard + trading)
│   │   │   ├── auth.py          # JWT authentication
│   │   │   ├── billing.py       # Paystack checkout and webhook
│   │   │   └── events.py        # WebSocket event streaming
│   │   └── middleware.py        # JWT auth middleware
│   ├── agents/
│   │   ├── engine.py            # Standard agent engine (Tool Use API)
│   │   ├── trading_engine.py    # Trading agent engine (MT5 + Claude)
│   │   ├── tasks.py             # Celery background tasks
│   │   └── tools/
│   │       ├── __init__.py      # Tool registry for Claude
│   │       ├── google_search.py # SerpAPI integration
│   │       ├── web_scraper.py   # ScraperAPI + BeautifulSoup
│   │       ├── email_tool.py    # Resend email API
│   │       ├── seo_tool.py      # SEO research tool
│   │       ├── upwork_tool.py   # Upwork job finder
│   │       ├── linkedin_tool.py # LinkedIn lead finder
│   │       ├── mt5_tool.py      # Deriv MT5 connection + trade execution
│   │       ├── ta_tool.py       # Technical analysis (EMA/RSI/MACD/BB/ATR)
│   │       └── news_tool.py     # Forex news and sentiment
│   ├── db/
│   │   ├── database.py          # Async session factory
│   │   └── models.py            # SQLAlchemy models (User, Agent, AgentEvent)
│   ├── services/
│   │   ├── paystack_service.py  # Paystack API wrapper
│   │   └── redis_service.py     # Redis pub/sub
│   ├── config.py                # Settings
│   ├── main.py                  # FastAPI app entry point
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── dashboard/           # Main dashboard
│   │   └── page.tsx             # Login / landing page
│   ├── components/
│   │   ├── AgentCard.tsx        # Agent display (standard + trading)
│   │   ├── DeployModal.tsx      # Deploy modal (AI agent + MT5 trader tabs)
│   │   └── LiveEventLog.tsx     # Real-time event stream
│   └── lib/
│       ├── api.ts               # API client
│       ├── store.ts             # Zustand auth store
│       └── websocket.ts         # WebSocket connection
├── docker-compose.yml           # PostgreSQL + Redis
└── run_system.ps1               # Windows: start/stop entire system
```

## Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL 14+
- Redis 7+
- Docker Desktop (for local PostgreSQL + Redis)
- MetaTrader5 terminal (for trading agents — Windows only)
- Paystack account
- Anthropic API account
- SerpAPI account (100 free searches/month)
- Resend account (3,000 free emails/month)
- ScraperAPI account (1,000 free credits/month)

### 1. Clone and install

```bash
git clone https://github.com/yourusername/openclaw.git
cd openclaw
```

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt
pip install MetaTrader5 beautifulsoup4 lxml httpx resend
```

```bash
# Frontend
cd frontend
npm install
```

### 2. Environment variables

**`backend/.env`**:
```env
DATABASE_URL=postgresql://openclaw:openclaw_secret@localhost:5432/openclaw_db
REDIS_URL=redis://localhost:6379
ANTHROPIC_API_KEY=your_anthropic_key
PAYSTACK_SECRET_KEY=sk_test_your_key
PAYSTACK_PUBLIC_KEY=pk_test_your_key
JWT_SECRET=your_minimum_32_char_secret
FRONTEND_URL=http://localhost:3000

# Tool API keys
SERPAPI_KEY=your_serpapi_key
RESEND_API_KEY=your_resend_key
RESEND_FROM_EMAIL=onboarding@resend.dev
SCRAPER_API_KEY=your_scraperapi_key

# Deriv MT5 (trading agents)
MT5_LOGIN=your_mt5_account_number
MT5_PASSWORD=your_mt5_password
MT5_SERVER=Deriv-Demo
```

**`frontend/.env.local`**:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_PAYSTACK_PUBLIC_KEY=pk_test_your_key
```

### 3. Start the system

```powershell
# Windows — starts Docker, backend, Celery, and frontend
.\run_system.ps1 start

# Stop everything
.\run_system.ps1 stop
```

Or manually:
```bash
docker-compose up -d                          # PostgreSQL + Redis
uvicorn backend.main:app --reload --port 8000 # Backend (run from project root)
celery -A backend.agents.tasks worker         # Celery worker
cd frontend && npm run dev                    # Frontend
```

### 4. Database setup

On first run, reset the database to create all tables:

```bash
cd backend
python -c "
import asyncio
from db.models import Base
from sqlalchemy.ext.asyncio import create_async_engine

async def reset():
    engine = create_async_engine('postgresql+asyncpg://openclaw:openclaw_secret@localhost:5432/openclaw_db')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print('Database ready!')

asyncio.run(reset())
"
```

## API Endpoints

### Authentication
- `POST /auth/register` — Create account
- `POST /auth/login` — Get JWT token

### Agents
- `GET /agents/` — List agents
- `POST /agents/deploy` — Deploy standard AI agent
- `POST /agents/deploy/trading` — Deploy MT5 trading agent
- `POST /agents/{id}/run` — Execute agent
- `DELETE /agents/{id}` — Delete agent
- `GET /agents/{id}/events` — Get event log

### Billing
- `POST /billing/checkout/{tier}` — Paystack checkout
- `POST /billing/webhook` — Paystack webhook

## Subscription Tiers

| Tier      | Price    | Agents | Notes                    |
|-----------|----------|--------|--------------------------|
| Free      | $0       | 1      | Standard agents only     |
| Starter   | $29/mo   | 2      | Standard + trading       |
| Empire    | $99/mo   | 10     | Standard + trading       |
| Unlimited | $299/mo  | ∞      | Standard + trading       |

## Trading Agents

Trading agents require:
1. A Deriv account with MT5 enabled — [deriv.com](https://deriv.com)
2. MT5 terminal installed and running on Windows
3. Demo account recommended for testing (2–4 weeks minimum before going live)

**Supported instruments:**
- Forex majors: EUR/USD, GBP/USD, USD/JPY, USD/CHF, AUD/USD, USD/CAD, NZD/USD
- Forex minors: EUR/GBP, EUR/JPY, GBP/JPY, EUR/CAD, GBP/CAD, AUD/CAD
- Commodities: Gold (XAU/USD), Silver (XAG/USD), WTI Oil, Brent Oil

**Stake levels:**
- Conservative: 0.01 lots (~$0.10/pip) — recommended for accounts under $500
- Moderate: 0.05 lots (~$0.50/pip) — recommended for $500–$2000
- Aggressive: 0.10 lots (~$1.00/pip) — recommended for $2000+

**Best trading times (EAT — Nairobi):**
- London session: 11:00 AM – 8:00 PM
- New York session: 4:00 PM – 1:00 AM
- London/NY overlap: 4:00 PM – 8:00 PM ← highest volume, best signals

## Deployment (Production)

- Backend: [Railway](https://railway.app)
- Frontend: [Netlify](https://netlify.com)
- Note: Trading agents must run locally or on a Windows VPS — MetaTrader5 Python library is Windows only

### Production checklist
- [ ] Switch Paystack keys to live (`sk_live_*`)
- [ ] Set `FRONTEND_URL` to your domain
- [ ] Enable HTTPS
- [ ] Register Paystack webhook: `https://your-domain.com/billing/webhook`
- [ ] Use strong `JWT_SECRET` (32+ chars)
- [ ] Switch MT5 server to `DerivSVG-Server` for live trading

## Paystack Webhook (Local Testing)

```bash
# Expose local backend with ngrok
ngrok http 8000
# Add https://your-ngrok-url/billing/webhook to Paystack dashboard
```

Test card: `4084 0840 8408 4081` | Expiry: any future date | CVV: any 3 digits

## License

MIT