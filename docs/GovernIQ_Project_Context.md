# GovernIQ — Complete Project Context Document

**Purpose:** This document gives any AI agent or new Kiro session full context on what GovernIQ is, what has been built, how it's architected, and what comes next. Paste this into a new workspace to get up to speed instantly.

**Last Updated:** July 2026
**Current Version:** v3.4.0
**Author:** Taiwo Durodola-Tunde

---

## 1. What Is GovernIQ?

GovernIQ is a production-grade Governance, Risk & Compliance (GRC) platform built with Python. It provides:

- Real-time compliance posture monitoring
- Quantitative risk scoring with weighted formulas
- Automated overdue risk escalation (4-tier)
- One-click Outlook email dispatch to risk owners
- Multi-page PDF management reports
- Full audit trail for governance evidence
- REST API for external integrations
- Jira bidirectional sync
- Dark/light mode with GovernIQ amber branding
- PostgreSQL persistent backend (Neon)
- Cloud deployment on Streamlit Community Cloud
- Password-gated access

---

## 2. Live Deployments

| Environment | URL | Purpose |
|-------------|-----|---------|
| **Cloud App** | https://grc-com.streamlit.app | Live dashboard (password: set in secrets) |
| **Landing Page** | https://taiwogold.github.io/grc-compliance-dashboard/ | Public marketing page |
| **GitHub Repo** | https://github.com/taiwogold/grc-compliance-dashboard | Source code (public) |
| **Database** | Neon PostgreSQL (eu-west-2) | Persistent cloud storage |

---

## 3. Technology Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | Streamlit 1.59 | Multi-tab interface |
| Charts | Plotly Express + Graph Objects | Theme-aware |
| Backend | Python 3.12 (local) / 3.14 (cloud) | |
| API | FastAPI | 9 REST endpoints |
| Database (cloud) | PostgreSQL via Neon | psycopg3 driver |
| Database (local) | SQLite | Auto-fallback |
| PDF | ReportLab | Multi-page with tables |
| Email | pywin32 COM (local) | Outlook automation |
| Auth | Custom password gate + RBAC module | bcrypt hashed |
| Hosting | Streamlit Community Cloud | Auto-deploys from GitHub |
| Landing Page | GitHub Pages | Static HTML in /docs |
| Version Control | Git + GitHub | Semantic versioning |

---

## 4. Project Architecture

```
grc-compliance-dashboard/
│
├── dashboard.py                  # Main UI — multi-tab orchestration (~350 lines)
│
├── api/
│   ├── __init__.py
│   ├── auth.py                   # API key authentication
│   └── main.py                   # FastAPI REST endpoints (9 routes)
│
├── utils/
│   ├── __init__.py               # Package exports (all modules)
│   ├── data_loader.py            # CSV loading, validation, caching
│   ├── metrics.py                # Compliance scoring, escalation logic
│   ├── charts.py                 # All Plotly chart generation
│   ├── pdf_generator.py          # Legacy + enhanced PDF reports
│   ├── email_dispatcher.py       # Outlook COM dispatch (original)
│   ├── risk_scoring.py           # Quantitative scoring engine
│   ├── database.py               # SQLite with multi-org support
│   ├── db_postgres.py            # PostgreSQL operations
│   ├── db_manager.py             # Smart backend switching (PG/SQLite)
│   ├── audit_trail.py            # Action logging
│   ├── alerts.py                 # Threshold detection & notifications
│   ├── theme.py                  # GovernIQ brand theming (dark/light)
│   ├── cloud_auth.py             # Password gate for cloud deployment
│   ├── auth.py                   # Full RBAC authentication
│   ├── config.py                 # Centralised env-based configuration
│   ├── jira_integration.py       # Jira REST API push/sync
│   ├── csv_validator.py          # Upload security validation
│   ├── rate_limiter.py           # Database-backed rate limiting
│   └── logger.py                 # Unified logging framework
│
├── email_providers/
│   ├── __init__.py
│   ├── base_provider.py          # Abstract email interface
│   ├── outlook_provider.py       # Outlook COM (Windows)
│   ├── smtp_provider.py          # SMTP provider
│   ├── sendgrid_provider.py      # SendGrid provider
│   └── mock_provider.py          # Testing mock
│
├── data/
│   ├── risk_register.csv         # Risk register (8 risks)
│   ├── controls.csv              # ISO 27001 controls (10 controls)
│   ├── compliance_history.csv    # Monthly scores (Jan-Jul)
│   └── grc_history.db            # SQLite (local, gitignored)
│
├── docs/
│   ├── index.html                # GovernIQ landing page
│   ├── GovernIQ_Agentic_Organisation_Playbook.md
│   └── GovernIQ_Project_Context.md (this file)
│
├── logs/                         # Email audit trail (gitignored)
├── .streamlit/
│   ├── config.toml               # GovernIQ theme config
│   └── secrets.toml              # Local secrets (gitignored)
│
├── requirements.txt              # Python dependencies
├── README.md                     # Full project documentation
└── .gitignore
```

---

## 5. Version History

| Version | Date | Features |
|---------|------|----------|
| v1.0.0 | Feb 2026 | Initial MVP dashboard |
| v1.1.0 | Mar 2026 | Compliance score, executive summary |
| v2.0.0 | Apr 2026 | Professional dashboard, heat maps, filters |
| v2.0.1 | Apr 2026 | Overdue risk escalation tracking |
| v2.0.2 | Apr 2026 | Monthly management reports, enhanced PDF |
| v2.1.0 | May 2026 | Outlook email integration |
| v2.1.1 | May 2026 | Modular refactor (utils package) |
| v2.2.0 | Jun 2026 | Risk scoring, SQLite history, audit trail, alerts, dark mode |
| v2.3.0 | Jun 2026 | Jira integration |
| v2.4.0 | Jun 2026 | Config management, multi-org DB, email providers, auth |
| v2.5.0 | Jul 2026 | Streamlit Cloud deployment, password gate |
| v3.0.0 | Jul 2026 | PostgreSQL backend (Neon) |
| v3.0.2 | Jul 2026 | CSV upload security validation |
| v3.0.3 | Jul 2026 | Unified logging framework |
| v3.1.0 | Jul 2026 | Database-backed rate limiting |
| v3.2.0 | Jul 2026 | FastAPI REST API (9 endpoints) |
| v3.3.0 | Jul 2026 | Multi-tab interface |
| v3.3.1 | Jul 2026 | Dark mode fix (comprehensive CSS) |
| v3.4.0 | Jul 2026 | GovernIQ branding, landing page, premium UI |

---

## 6. Key Features Implemented

### Dashboard (6 tabs)
- 📊 Executive — KPIs, compliance trend, ISO coverage, owner summary
- ⚠️ Risks & Scoring — heat map, scoring engine, top risks, full register
- 🔥 Escalations — overdue risks, 4-tier levels, timeline, upcoming dues
- 📈 History & Trends — snapshots, delta analysis, individual tracking, monthly summary
- 📧 Communications — Outlook dispatch, bulk send, email directory
- 📥 Reports & Exports — CSV/PDF downloads, audit trail, database status

### Risk Scoring Formula
```
Residual Score = (Likelihood × Impact) × Overdue_Modifier × Control_Modifier

Overdue: 1.0 + (days_overdue × 0.02), capped at 2.0
Control: Implemented=0.5, In Progress=0.75, Planned=1.0

Bands: Critical(≥15), High(≥10), Medium(≥5), Low(<5)
```

### Escalation Tiers
- Level 1 (1-14 days): Owner Reminder
- Level 2 (15-30 days): Manager Escalation
- Level 3 (31-60 days): Director Escalation
- Level 4 (60+ days): Executive Escalation

### REST API Endpoints
- GET /api/v1/health (no auth)
- GET /api/v1/risks (filterable)
- GET /api/v1/risks/{id}
- GET /api/v1/compliance
- GET /api/v1/controls
- GET /api/v1/escalations
- GET /api/v1/scores
- GET /api/v1/snapshots
- GET /api/v1/audit

### Database Manager
- Auto-detects: PostgreSQL if configured → SQLite fallback
- Same API regardless of backend
- Snapshot capture (1 per day)
- Audit trail logging
- Risk history tracking

---

## 7. Brand Identity

| Element | Value |
|---------|-------|
| Name | GovernIQ |
| Tagline | Intelligent Governance. Clear Risk. |
| Primary Colour | Amber #F59E0B |
| Hover/Pressed | Saffron #D97706 |
| Highlight | Sunrise #FCD34D |
| Dark Background | Charcoal #1C1917 |
| Light Background | Warm Stone #F5F5F4 |
| Secondary Text | Smoke #78716C |
| Critical/Danger | Deep Ember #92400E |
| Personality | Professional, warm, trustworthy |

---

## 8. Data Model

### Risk Register (CSV)
```
Risk_ID, Risk_Name, Risk_Level, Likelihood, Impact, Status,
Control_Status, Risk_Owner, Owner_Email, Due_Date
```

### Controls (CSV)
```
Control, Status (Implemented/In Progress/Planned)
```

### PostgreSQL Tables
- risk_snapshots (daily point-in-time captures)
- risk_history (individual risk records per snapshot)
- audit_trail (all dashboard actions)
- compliance_trend (historical scores)

### SQLite Tables (local fallback)
- organizations (multi-tenant)
- snapshots (same as PG)
- risk_history (same as PG)
- audit_trail (same as PG)
- rate_limits (per-action daily/hourly counters)

---

## 9. Security Design

| Control | Implementation |
|---------|---------------|
| No hardcoded credentials | All secrets in st.secrets or .env |
| Email via existing session | Outlook COM, no passwords stored |
| Rate limiting | DB-backed, daily + hourly windows |
| Input validation | CSV validator, email format checks |
| Content sanitisation | Null byte removal, injection prevention |
| Audit logging | Every action timestamped |
| Password gate | Cloud deployment protected |
| RBAC ready | Admin/Manager/Viewer roles |
| API key auth | X-API-Key header required |
| SSL enforced | PostgreSQL sslmode=require |

---

## 10. What's Next (Roadmap)

### Near-term (v3.5 - v3.9)
- Teams webhook notifications
- Excel/JSON/HTML export formats
- Performance & pagination
- Help system & tooltips
- Additional themes (corporate, colourblind-safe)
- Dynamic validation rules engine

### Medium-term (v4.0)
- Competition-ready MVP polish
- Mobile responsive layout
- Database backup automation
- Onboarding flow for new users

### Long-term (v5.0+)
- Microsoft Graph API (replace COM)
- Azure AD SSO
- Vulnerability data ingestion (Nessus/Qualys)
- Multi-framework (ISO 27001, NIST CSF, CIS)
- Power BI embedded
- Multi-department views
- White-label offering

---

## 11. Autonomous Agentic Organisation

GovernIQ is designed to be operated by a full autonomous AI organisation:

- **9 C-suite agents** (CTO, CPO, COO, CMO, CRO, CSO, CIO, CGO + CEO human)
- **24 operational agents** across Engineering, Product, Ops, Marketing, Revenue, Security, Finance, Grants
- **33 total roles** defined with responsibilities, authority levels, and system prompts
- **Full playbook** at: `docs/GovernIQ_Agentic_Organisation_Playbook.md`

---

## 12. Key Files to Read First

When starting in a new workspace, read these in order:
1. This file (`GovernIQ_Project_Context.md`) — full context
2. `dashboard.py` — main application entry point
3. `utils/__init__.py` — all module exports
4. `utils/db_manager.py` — database switching logic
5. `.streamlit/config.toml` — theme and server config
6. `requirements.txt` — all dependencies
7. `docs/GovernIQ_Agentic_Organisation_Playbook.md` — org structure

---

## 13. Environment Setup

### Local Development
```bash
git clone https://github.com/taiwogold/grc-compliance-dashboard.git
cd grc-compliance-dashboard
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install pywin32  # Windows only, for Outlook
streamlit run dashboard.py
```

### Cloud (Streamlit Community Cloud)
- Deployed from `main` branch automatically
- Secrets configured in Streamlit Cloud Settings panel
- PostgreSQL via Neon (eu-west-2)
- pywin32 not available (graceful fallback)

### Secrets Format (Streamlit Cloud)
```toml
[passwords]
dashboard_password = "your_password"

[app]
environment = "production"

[database]
url = "postgresql://user:pass@host/db?sslmode=require"

[api]
keys = ["key1", "key2"]
```

---

## 14. Common Issues & Solutions

| Issue | Cause | Fix |
|-------|-------|-----|
| ImportError from utils | Stale __pycache__ or need restart | `sys.dont_write_bytecode = True` in dashboard.py + restart Streamlit |
| Outlook Not Available | pywin32 missing or Outlook not running | Install pywin32 + open Outlook (Windows only) |
| PostgreSQL auth failed | Wrong password in secrets | Reset in Neon → update Streamlit secrets |
| psycopg install fails on cloud | Python 3.14 compat | Use `psycopg[binary]>=3.2.10` (not pinned) |
| SQLite "no such table" | DB file deleted or schema mismatch | Delete `data/grc_history.db`, let it recreate |
| Theme looks broken | CSS fighting Streamlit | Full comprehensive CSS override in theme.py |

---

*This document is the single source of truth for any new AI session working on GovernIQ.*
*GovernIQ — Intelligent Governance. Clear Risk.*
