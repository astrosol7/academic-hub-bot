# 🪐 Academic Hub — Orbit Release (v1.0)

[![Stability: Production](https://img.shields.io/badge/Stability-Production-emerald.svg)](https://github.com/astrosol7/academic-hub-bot)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Engine: PostgreSQL](https://img.shields.io/badge/Engine-PostgreSQL-336791.svg)](https://www.postgresql.org/)

The **Academic Hub** is a high-performance, search-driven academic retrieval engine. It transforms fragmented institutional resources into a structured, searchable, and secure knowledge graph accessible via Telegram and managed through a premium administrative dashboard.

---

## 🏛 System Architecture

The Orbit Release marks the transition from a prototype to a **distributed intelligence system**.

| Component | Responsibility | Stack |
|:--- |:--- |:--- |
| **Telegram UI** | High-concurrency user interface & delivery | Aiogram 3, FSM, Asyncio |
| **FastAPI Gateway** | Auth, Ingestion API, Search Bridge | FastAPI, SQLAlchemy, Pydantic |
| **PostgreSQL Core** | Relational brain & telemetry storage | Postgres 16, pg_trgm, TSVector |
| **Orbit Dashboard** | Multi-tenant governance & Incident War Room | React, Vite, Lucide, Tailwind v4 |

### 🔍 Intelligence Flow
1. **Request**: User types "Calculus 1 lecture notes" in Telegram.
2. **Analysis**: Bot classifies intent and calls the **FastAPI Search Bridge**.
3. **Retrieval**: Gateway queries PostgreSQL using **TSVector (Exact)** + **Trigram (Fuzzy)** ranking.
4. **Delivery**: Bot delivers structured materials with atomic progress tracking.
5. **Telemetry**: Behavioral signals are flushed to `usage_signals` for future AI training.

---

## 🍼 Quick Start (The "Baby Guide")

If you are new to this, just follow these exact steps. Do not skip any!

### Step 1: Open your Terminal
Open your terminal (PowerShell or Command Prompt) and move into the project folder.

### Step 2: Create a Secret Room (Virtual Environment)
This keeps the project's tools separate from your computer's tools.
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Tell the System your Secrets
Create a file named `.env` in the main folder and paste this in (replace the values with your actual keys):
```env
TELEGRAM_BOT_TOKEN="your_bot_token_from_botfather"
DATABASE_URL="postgresql://postgres:password@localhost:5432/academic_hub"
BOOTSTRAP_ROOT_PASSWORD="PickAStrongPassword"
JWT_SECRET="MakeUpALongRandomString"
```

### Step 4: Wake up the Database
If you have Docker, run:
```powershell
docker-compose up -d
```

### Step 5: Start the Bot (The Face)
In your first terminal, run:
```powershell
python -m academic_hub.app
```

### Step 6: Start the Dashboard (The Control Room)
Open a **second terminal**, go into the `dashboard` folder, and run:
```powershell
cd dashboard
npm install
npm run dev
```

### Step 7: Give yourself "Super Power" (Admin Setup)
The very first time you use the system, you must create your Admin account. Open a **third terminal** and run:
```powershell
curl -X POST http://localhost:8000/api/v1/auth/bootstrap `
  -H "Content-Type: application/json" `
  -d '{"username": "admin", "password": "ThePasswordYouPickedInStep3"}'
```
*Wait! If you see a success message, you are now the boss. The "bootstrap" button is now locked forever for safety.*

---

## 🔒 Security & Hardening

Orbit v1 is designed to be **unbreakable** under standard academic operation.

*   **Zero Leakage**: All sensitive keys (`.env`, JWT) and heavy assets are strictly blocked via `.gitignore`.
*   **HTML Sanitization**: Every user-generated string is escaped before rendering to prevent Telegram HTML injection.
*   **Dual-Token Auth**: Dashboard sessions use short-lived Access Tokens (30m) and long-lived Refresh Tokens (7d).
*   **CIS Gates**: The Controlled Ingestion System prevents "data poisoning" via strict schema validation and fuzzy duplicate detection.

---

## 📊 Behavioral Matrix (Telemetry)

We don't just store files; we store **insights**.

*   **Tier 1 (Raw)**: `usage_signals` — Every search, click, and navigation. (Pruned every 90 days).
*   **Tier 2 (Aggregated)**: `usage_aggregates` — Search frequency and resource popularity.
*   **Tier 3 (Permanent)**: `usage_insights` — Strategic data on material gaps and student needs.

---

## 📁 Repository Overview
```text
SIT_Academic_Hub_bot/
├── academic_hub/     # The Telegram Engine (Intent, Delivery, UI)
├── backend/          # The Brain (FastAPI, Auth, Ingest, Search)
├── dashboard/        # The Control Tower (React/Vite Admin UI)
├── resources/        # Local asset cache (Gitignored)
├── .env              # Secrets (NEVER COMMIT)
└── README.md         # This manual
```

**Orbit Release v1.0 — Stabilized, Integrated, Ready.**
