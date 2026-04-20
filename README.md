<div align="center">
  <img src="https://img.shields.io/badge/ORBIT-v1.0-blueviolet?style=for-the-badge&logo=spaceX" alt="Orbit Release" />
  <h1>🪐 SIT Academic Hub</h1>
  <p><strong>The Ultimate Academic Knowledge Engine & Telemetry System</strong></p>

  [![Stability: Production](https://img.shields.io/badge/Stability-Production-emerald.svg)](https://github.com/astrosol7/academic-hub-bot)
  [![Engine: PostgreSQL](https://img.shields.io/badge/Engine-PostgreSQL-336791.svg?logo=postgresql)](https://www.postgresql.org/)
  [![Core: FastAPI](https://img.shields.io/badge/Core-FastAPI-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
  [![Bot: Aiogram 3](https://img.shields.io/badge/Bot-Aiogram_3-blue.svg?logo=telegram)](https://docs.aiogram.dev/)
  [![UI: React + Vite](https://img.shields.io/badge/UI-React_Vite-61DAFB.svg?logo=react)](https://reactjs.org/)

</div>

---

## 🚀 Mission Objective
**Academic Hub (Orbit Release)** is a premium, enterprise-grade educational resource orchestrator. Designed for lightning-fast retrieval, it transforms scattered academic files into a heavily structured, strictly formatted **Knowledge Graph** accessible natively through Telegram and an interactive Web App, governed by a beautiful glassmorphism React Administrative Dashboard.

Gone are the days of endless folder diving. Submit a query, and Orbit delivers your exact course material instantly.

---

## 🌌 The Orbit Constellation (Architecture)
The platform is radically modular, utilizing a master `launcher` to orchestrate 4 isolated sub-systems simultaneously.

```mermaid
graph TD;
    A[Student] -->|Telegram Bot| B(Aiogram Engine);
    A -->|Mini App| C(Voyager WebUI);
    B --> D{FastAPI Core};
    C --> D;
    E[Admins] -->|Dashboard| F(Orbit Control Tower);
    E -->|Electron Desktop| G(Control Center);
    F --> D;
    G --> D;
    D <--> H[(PostgreSQL Vector DB)];
```

---

## 🏗️ Project Structure
Everything has been meticulously organized into autonomous modules to prevent spaghetti code and enforce clean system design boundaries.

```text
SIT_Academic_Hub_bot/
├── src/                          # System Core & Logic
│   ├── bot/                      # Telegram Intelligence (Aiogram 3 FSM)
│   ├── core/                     # Shared Models, Intent Parsing & Analytics
│   └── tests/                    # Security and Core Module Tests
├── backend/                      # High-Concurrency FastAPI Gateway
│   └── api/                      # Routes, JWT Auth, CIS Ingestion
├── dashboard/                    # React + Vite Multi-tenant Admin Dashboard
├── student_app/                  # 'Voyager' Telegram Mini-App (Vite)
├── desktop-app/                  # Electron Desktop Client for Admins
├── scripts/                      # Bootstrap tools & LMS Scrapers
│   └── lms_scraper/              # Moodle deep-crawlers
├── data/                         # Persistent DB caches & SQLite mirrors
├── resources/                    # Academic Document File Storage
├── launcher.py                   # The Master Orbit Process Orchestrator
└── orbit.cmd                     # Global CLI executable wrapper
```

---

## 🔥 Features

### 1. 🔍 Dual-Engine Search
Powered by PostgreSQL, our search engine utilizes rigorous **TSVector** full-text lookup for exact metadata hits. If you make a typo, it instantly falls back to a generalized **trigram (`pg_trgm`)** proximity scan guaranteeing a match.

### 2. 🛡 Advanced Telemetry & Identity Matrix
The Dashboard tracks every failed search parameter and logs it as a **Knowledge Gap** incident for admins to review. In parallel, the bot strictly binds authorized Telegram IDs directly to institutional student database records to prevent unauthorized infiltrations.

### 3. 🛸 The Orbit Launcher
Bringing up 5 concurrent servers (Vite, API, DB, Bot) is difficult. We built `launcher.py`—a heavily stylized orchestration tool that cleans local ports, tests credentials, and lifts everything with animated ASCII statuses in a single unified terminal window.

---

## ⚙️ Quick Start (Deploying Orbit)

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **PostgreSQL 16** (Service running locally or in Docker)

### 1️⃣ Ignition Sequence
Ensure your `.env` is configured correctly at the root folder:
```env
TELEGRAM_BOT_TOKEN="your_token"
DATABASE_URL="postgresql://postgres:password123@localhost:5432/academic_hub"
POSTGRES_PASSWORD="password123"
BOOTSTRAP_ROOT_PASSWORD="StrongRootPassword"
JWT_SECRET="CHANGE_ME_LONG_RANDOM"
ORBIT_BOT_API_KEY="CHANGE_ME_SHARED_BOT_KEY"
ORBIT_BACKEND_BASE_URL="http://127.0.0.1:8000"
```

### 2️⃣ Initialize Database & Install Requirements
```powershell
pip install -r requirements.txt
npm install --prefix dashboard
npm install --prefix student_app
```

### 3️⃣ Launch!
Run the setup script once to bind Orbit to your PC environment:
```powershell
.\setup_cli.ps1
```
Now, in any terminal, simply type:
```powershell
orbit
```
> **Isolated Bot Mode:** If you just want to develop the bot logic without the heavy React UI, type `orbit --bot-only`.

---

## 🔒 Security Best Practices
- **Controlled Ingestion System (CIS):** Admin uploads are checked via fuzzy-matching hashes to actively quarantine duplicate documents.
- **Git Policy:** Comprehensive `legacy/` tracking and rigorous `.gitignore` execution ensure DB dumps and `.pem` certificates never leak onto GitHub.
- **Micro-interactions:** Delivery sessions hold discrete cancellation protocols with FSM tracking preventing token injection or navigation leakages across asynchronous loops.

---

<div align="center">
  <p><i>"Stabilizing the Universe, one commit at a time."</i></p>
  <p><b>— v 1.0 Stable</b></p>
</div>
