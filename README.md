# 🪐 Academic Hub — Orbit Release (v1.0)

[![Stability: Production](https://img.shields.io/badge/Stability-Production-emerald.svg)](https://github.com/astrosol7/academic-hub-bot)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Engine: PostgreSQL](https://img.shields.io/badge/Engine-PostgreSQL-336791.svg)](https://www.postgresql.org/)
[![UI: Premium Dashboard](https://img.shields.io/badge/UI-Orbit_Control-blueviolet.svg)](https://github.com/astrosol7/academic-hub-bot)

The **Academic Hub** is a high-performance, search-driven academic retrieval engine. It transforms fragmented institutional resources into a structured, searchable, and secure knowledge graph accessible via Telegram and managed through a premium administrative dashboard.

The **Orbit Release (v1.0)** marks the transition from a prototype to a **distributed intelligence system**, where all metadata and content relations are centralized in a unified PostgreSQL backend.

---

## 🏛 System Architecture

The Academic Hub is built on a resilient, three-tier architecture designed for scalability and high concurrency.

| Component | Responsibility | Stack |
|:--- |:--- |:--- |
| **Telegram Intelligence** | High-concurrency student interface & material delivery | Aiogram 3, FSM, Asyncio |
| **FastAPI Gateway** | Unified API, JWT Auth, CIS Ingestion, Search Bridge | FastAPI, SQLAlchemy, Pydantic |
| **PostgreSQL Core** | Relational brain & telemetry storage | Postgres 16, pg_trgm, TSVector |
| **Orbit Dashboard** | Multi-tenant governance & Identity Matrix | React, Vite, Lucide, Tailwind v4 |

### 🔍 Unified Intelligence Flow
1. **Contextual Search**: The **Search Bridge** utilizes a dual-engine approach, combining **TSVector Full-Text Search** for precision with **`pg_trgm` Trigram Fallback** for typo-tolerance.
2. **Deterministic Navigation**: The bot's core navigation (Quarters → Courses → Weeks) is now fully database-driven, ensuring a single source of truth across all platforms.
3. **Atomic Delivery**: Intelligent background task management ensures large material bundles are delivered reliably without blocking the user interface.
4. **Behavioral Telemetry**: Every interaction is captured as a "Signal" and aggregated into "Insights" for institutional gap analysis.

---

## 🛰 Orbit Control (Admin Dashboard)

The **Orbit Control Tower** provides a glassmorphism-inspired administrative interface for institutional governance.

*   **🛡 Identity Matrix**: A state-of-the-art interface for binding Telegram IDs to institutional student records, with built-in conflict resolution.
*   **⚠️ Incident War Room**: Real-time triage for student-reported issues (missing files, wrong content) with direct database tracking.
*   **📊 Search Intelligence**: Advanced analytics that reveal "Material Gaps" (failed queries), allowing admins to prioritize resource acquisition.
*   **🧼 Quarantine Station**: A security gate for scanning and neutralizing filesystem anomalies before they are ingested into the core database.

---

## 🍼 Quick Start

### 📋 Prerequisites
- **Python 3.10+**
- **PostgreSQL 16** (or Docker Desktop)
- **Node.js 18+** (for the Dashboard)

### 🚀 Implementation Steps

1. **Environment Configuration**:
   Create a `.env` file in the root directory:
   ```env
   TELEGRAM_BOT_TOKEN="your_bot_token"
   DATABASE_URL="postgresql://postgres:password@localhost:5432/academic_hub"
   BOOTSTRAP_ROOT_PASSWORD="StrongRootPassword"
   JWT_SECRET="LongRandomString"
   ```

2. **Initialize Infrastructure**:
   ```powershell
   # Start Database
   docker-compose up -d
   
   # Synchronize Metadata & Ingest Resources
   python -m backend.sync.sync_service
   ```

3. **Deploy Components**:
   ```powershell
   # Terminal 1: Telegram Bot
   python -m academic_hub.app
   
   # Terminal 2: Galactic Dashboard
   cd dashboard; npm install; npm run dev
   ```

4. **Administrator Bootstrap**:
   On first run, create your root account via the security gateway:
   ```powershell
   curl -X POST http://localhost:8000/api/v1/auth/bootstrap `
     -H "Content-Type: application/json" `
     -d '{"username": "admin", "password": "YourRootPassword"}'
   ```

---

## 🔒 Security & Hardening

*   **CIS Gates**: The **Controlled Ingestion System** enforces strict schema validation and fuzzy duplicate detection for all new resources.
*   **Dual-Token Auth**: Dashboard sessions utilize short-lived Access Tokens (30m) and long-lived Refresh Tokens (7d) for maximum security.
*   **Zero Leakage**: Strict `.gitignore` policy ensures sensitive institutional data and private keys never leave the local environment.

---

**Orbit Release v1.0 — Unified, Intelligent, Unbreakable.**
