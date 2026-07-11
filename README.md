# 🛡️ GRC Compliance Dashboard

A production-grade Governance, Risk & Compliance dashboard built with Python, Streamlit and Plotly. Delivers real-time visibility into risk posture, compliance metrics, ISO 27001 control effectiveness, escalation tracking, automated remediation workflows, and intelligent alerting.

Designed for Cyber Security Governance & Assurance teams to provide executive-level reporting, reduce manual administration, and drive accountability across risk owners.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.59-red?logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-6.8-purple?logo=plotly&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-2.5.0-orange)

---

## Overview

This project transforms raw risk and compliance data into actionable executive reporting through interactive dashboards, intelligent alerting, automated email dispatch, and professional PDF management reports.

**What it enables:**

- Real-time compliance posture monitoring with RAG health rating
- Quantitative risk scoring with weighted formula
- Automated threshold alerts surfaced at the top of the dashboard
- Risk history tracking with daily SQLite snapshots and delta analysis
- One-click Outlook email dispatch to risk owners (zero stored credentials)
- Multi-page PDF management reports with sign-off sections
- Full audit trail for governance evidence
- Dark mode toggle for presentations and personal preference

---

## Live Dashboard

```bash
streamlit run dashboard.py
```

Opens at `http://localhost:8501`

---

## Architecture

```text
grc-compliance-dashboard/
│
├── dashboard.py                 # UI layout & orchestration (lean)
│
├── utils/
│   ├── __init__.py              # Package exports
│   ├── data_loader.py           # CSV loading, validation, caching
│   ├── metrics.py               # Compliance scoring, escalation logic
│   ├── charts.py                # All Plotly chart generation
│   ├── pdf_generator.py         # Legacy + enhanced PDF reports
│   ├── email_dispatcher.py      # Secure Outlook COM integration
│   ├── risk_scoring.py          # Quantitative risk scoring engine
│   ├── database.py              # SQLite history & snapshot storage
│   ├── audit_trail.py           # Action logging for governance evidence
│   ├── alerts.py                # Threshold detection & notifications
│   └── theme.py                 # Light/dark mode theming
│
├── data/
│   ├── risk_register.csv        # Risk register source data
│   ├── controls.csv             # ISO 27001 control matrix
│   ├── compliance_history.csv   # Monthly compliance scores
│   └── grc_history.db           # SQLite snapshot & audit database
│
├── logs/
│   └── email_audit.csv          # Email dispatch audit trail
│
├── .streamlit/
│   └── config.toml              # Streamlit theme configuration
│
├── assets/
│   └── banner.png               # Optional dashboard banner
│
├── requirements.txt
├── .gitignore
└── README.md
```

The application follows a **modular architecture** — `dashboard.py` is a thin orchestration layer that imports all business logic from purpose-built utility modules. Each module is independently testable and maintainable.

---

## Features

### Core Dashboard

| Feature | Description |
|---------|-------------|
| **Executive KPIs** | Compliance score, open/closed/high risk counts with delta indicators |
| **Health Rating** | RAG status (Green/Amber/Red) based on compliance thresholds |
| **Risk Heat Map** | Likelihood × Impact density heatmap |
| **Risk Distribution** | Bar chart by severity level (colour-coded) |
| **Open vs Closed** | Pie chart showing remediation progress |
| **Risk Owner Summary** | Aggregated view by team with open/high counts |
| **Interactive Filters** | Sidebar filtering by risk owner |
| **CSV Upload** | Upload custom risk register data on-the-fly |
| **Dark Mode** | Toggle between light and dark themes |

### Risk Scoring Engine (v2.2.0)

| Feature | Description |
|---------|-------------|
| **Weighted Formula** | Score = (Likelihood × Impact) × Overdue Modifier × Control Modifier |
| **Overdue Penalty** | Risks penalised up to 2× base score based on days overdue |
| **Control Credit** | Implemented controls reduce score by 50% |
| **Score Bands** | Critical (≥15), High (≥10), Medium (≥5), Low (<5) |
| **Top 5 Risks** | Executive widget showing highest-scored risks |
| **Distribution Chart** | Bar chart of score band breakdown |

### Trend Alerts & Notifications (v2.2.0)

| Feature | Description |
|---------|-------------|
| **Compliance Alert** | Triggered when score drops below 75% |
| **High Risk Alert** | Triggered when high risks exceed 3 |
| **Executive Escalation** | CRITICAL alert for any Level 4 escalation |
| **Trend Detection** | Warns when open risks increase vs last snapshot |
| **Closure Rate** | Info alert when closure rate falls below 20% |
| **Severity Sorting** | CRITICAL → WARNING → INFO display order |

### Risk History & Snapshots (v2.2.0)

| Feature | Description |
|---------|-------------|
| **Daily Snapshots** | Automatic point-in-time capture (one per day) |
| **SQLite Storage** | Persistent local database in `data/grc_history.db` |
| **Delta Analysis** | Compare current state vs previous snapshot |
| **Individual Tracking** | View how any risk evolved over time |
| **Score Trends** | Line chart showing risk score movement |

### Audit Trail (v2.2.0)

| Feature | Description |
|---------|-------------|
| **Action Logging** | Records loads, uploads, emails, exports |
| **SQLite Storage** | Persistent, queryable, indexed |
| **Filterable View** | Filter by action type in dashboard |
| **CSV Export** | Download full trail for compliance evidence |
| **Session Aware** | Avoids duplicate load entries |

### Compliance & Controls

| Feature | Description |
|---------|-------------|
| **Compliance Score** | Percentage of implemented controls vs total |
| **ISO 27001 Coverage** | Pie chart of Implemented / In Progress / Planned |
| **Compliance Trend** | Line chart tracking monthly score movement |
| **Target Threshold** | Visual target line at 80% for governance reporting |

### Escalation Tracking (v2.0.1)

| Feature | Description |
|---------|-------------|
| **Due Date Logic** | Automatic calculation of days overdue per risk |
| **4-Tier Escalation** | Level 1 (Owner) → Level 2 (Manager) → Level 3 (Director) → Level 4 (Executive) |
| **Overdue Dashboard** | Dedicated section with KPIs, tables, and timeline charts |
| **Upcoming Risks** | Early warning for risks due within 14 days |

### Monthly Management Reports (v2.0.2)

| Feature | Description |
|---------|-------------|
| **Month-over-Month Delta** | Compliance score movement with +/- indicator |
| **Risk Closure Rate** | Percentage of risks resolved vs total |
| **Gap-to-Target** | Distance from 80% compliance threshold |
| **Dynamic Recommendations** | Auto-generated actions based on current data state |
| **Enhanced PDF Export** | 5-page professional report with sign-off section |

### Outlook Integration (v2.1.0)

| Feature | Description |
|---------|-------------|
| **COM Automation** | Uses existing Outlook session (zero stored credentials) |
| **Individual Reminders** | Select owner → preview → confirm → send |
| **Bulk Dispatch** | One-click to notify all overdue risk owners |
| **Rate Limiting** | Max 20 emails per session (configurable) |
| **Audit Trail** | Every dispatch logged |
| **Input Validation** | Email format checks, injection prevention |
| **Confirmation Required** | Checkbox + button before any dispatch |

### Configuration Management (v2.4.0)

| Feature | Description |
|---------|-------------|
| **Centralised Config** | Single `utils/config.py` — no hardcoded paths anywhere |
| **.env File Support** | Local development config via `.env` file |
| **Environment Variables** | All paths, limits, and provider settings overridable |
| **Auto Directory Creation** | `data/` and `logs/` created automatically on startup |

### Email Provider Abstraction (v2.4.0)

| Feature | Description |
|---------|-------------|
| **Pluggable Providers** | Switch between Outlook, SMTP, SendGrid, or Mock |
| **Outlook Provider** | Existing COM behaviour preserved (Windows, no credentials stored) |
| **SMTP Provider** | Works on any OS — Office 365, Gmail, corporate relay |
| **SendGrid Provider** | Cloud-native HTTP API — no desktop client required |
| **Mock Provider** | In-memory capture for testing — no real emails sent |
| **Provider Factory** | Set `GRC_EMAIL_PROVIDER` in `.env` to switch providers |

### Authentication (v2.4.0)

| Feature | Description |
|---------|-------------|
| **Optional Login Screen** | Enabled via `GRC_AUTH_ENABLED=1` in `.env` |
| **bcrypt Password Hashing** | Passwords never stored in plain text |
| **Role-Based Access** | Admin and Viewer roles |
| **Session Cookies** | 1-day session cookie with configurable secret key |
| **Sidebar User Badge** | Shows logged-in user name and role |
| **Graceful Bypass** | Auth disabled by default — zero change for existing users |

### Multi-Organisation Database (v2.4.0)

| Feature | Description |
|---------|-------------|
| **Organizations Table** | Named organisations with auto-created default org |
| **Row-Level Isolation** | All queries filtered by `organization_id` |
| **Auto Migration** | Existing databases upgraded automatically on startup |
| **Connection Pooling** | Context manager prevents connection leaks |

### Jira Integration (v2.3.0)

| Feature | Description |
|---------|-------------|
| **Push Single Risk** | Push any individual risk to Jira as a tracked issue |
| **Bulk Push** | Push all open risks or high-severity risks in one click |
| **Duplicate Detection** | Checks for existing issues before creating to prevent duplicates |
| **Two-Way Sync** | Pull current Jira status back into the dashboard |
| **Mismatch Detection** | Flags risks marked Done in Jira but still Open in GRC |
| **Priority Mapping** | High/Medium/Low maps automatically to Jira priority |
| **Audit Logging** | Every push and sync recorded in the GRC audit trail |
| **Graceful Degradation** | Dashboard loads normally if Jira is unreachable |

### Dark Mode (v2.2.0)

| Feature | Description |
|---------|-------------|
| **Sidebar Toggle** | One-click light/dark switch |
| **Custom CSS Injection** | Backgrounds, cards, borders all theme-aware |
| **Chart Theming** | Plotly charts adapt to active theme |
| **Presentation Ready** | Dark mode ideal for board room displays |

---

## Security Design

| Control | Implementation |
|---------|---------------|
| No stored credentials | COM uses existing authenticated Outlook session |
| Corporate routing | All emails go via Exchange (DLP, retention, audit) |
| Rate limiting | Session-based cap prevents accidental mass-mailing |
| Input validation | Email format validation, injection char blocking |
| Content sanitisation | Null byte removal, dangerous character filtering |
| Audit logging | Timestamped log of every dispatch and action |
| Explicit confirmation | Double-confirmation UI before send |
| No hidden recipients | Individual emails only (no BCC) |

---

## Installation

### Prerequisites

- Python 3.10+
- Microsoft Outlook desktop client (for email features)
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/YOUR-USERNAME/grc-compliance-dashboard.git
cd grc-compliance-dashboard

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run

```bash
streamlit run dashboard.py
```

---

## Cloud Deployment (Streamlit Cloud)

The dashboard is cloud-ready and can be deployed to [Streamlit Community Cloud](https://share.streamlit.io) for free.

### Deploy Steps

1. **Push to GitHub** (your repo is already public ✅)

2. **Go to** [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub

3. **Click** "New app" → select your repo → set main file to `dashboard.py`

4. **Set secrets** in the app's Settings → Secrets panel:
   ```toml
   [passwords]
   dashboard_password = "YourSecurePassword123"
   
   [app]
   environment = "production"
   ```

5. **Deploy** — your app will be live at `https://your-app.streamlit.app`

### Cloud Notes

- **Password gate:** Visitors must enter the password you set in Secrets
- **Outlook email:** Not available on cloud (Windows-only). Dashboard gracefully shows "Not Available"
- **SQLite database:** Works on cloud but resets on each reboot (use PostgreSQL for persistent data in v3.0)
- **Requirements:** Streamlit Cloud uses `requirements.txt` — pywin32 will fail silently on Linux (handled gracefully)

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Streamlit |
| **Data Processing** | Pandas, NumPy |
| **Visualisation** | Plotly Express, Plotly Graph Objects |
| **Database** | SQLite (risk history, audit trail) |
| **PDF Generation** | ReportLab (SimpleDocTemplate, Tables, Styles) |
| **Email Dispatch** | pywin32 (Outlook COM automation) |
| **Jira Integration** | Jira REST API v3 (requests, Basic Auth with API token) |
| **Version Control** | Git, GitHub |

---

## Version History

| Version | Release | Features |
|---------|---------|----------|
| **v2.4.0** | Current | Config management, multi-org DB schema, pluggable email providers (Outlook/SMTP/SendGrid), authentication, improved error handling |
| **v2.3.0** | ✅ | Jira integration — push risks as issues, sync statuses, mismatch detection |
| **v2.2.0** | ✅ | Risk scoring, SQLite history, audit trail, trend alerts, dark mode |
| **v2.1.1** | ✅ | Modular refactor — extracted utils package |
| **v2.1.0** | ✅ | Outlook integration, automated reminder dispatch |
| **v2.0.2** | ✅ | Monthly management reports, enhanced PDF exports |
| **v2.0.1** | ✅ | Overdue risk escalation tracking, due date logic |
| **v2.0.0** | ✅ | Professional dashboard with heat maps, filters, ISO coverage |
| **v1.1.0** | ✅ | Compliance score, executive summary |
| **v1.0.0** | ✅ | Initial MVP dashboard |

---

## Roadmap

### v3.0.0 — Enterprise

- [ ] User authentication (Azure AD / SSO)
- [ ] SQL database backend (PostgreSQL)
- [ ] Role-based access control (RBAC)
- [ ] Full audit trail with user attribution
- [ ] Power BI integration
- [ ] Microsoft Graph API for email
- [ ] Vulnerability data ingestion
- [ ] Multi-department reporting
- [ ] Compliance framework selector (ISO 27001, NIST, CIS)
- [ ] Microsoft Teams webhook notifications

---

## Use Cases

**Governance & Assurance**
- Monthly risk reporting to governance committees
- Control effectiveness monitoring
- Compliance status reviews and board packs

**Security Risk Management**
- Risk heat mapping and quantitative scoring
- Remediation tracking and escalation
- Trend analysis with proactive alerting

**Audit & Compliance**
- ISO 27001 control coverage reporting
- Full audit trail for evidence packs
- Point-in-time risk snapshots for audit review

**Leadership Reporting**
- Executive dashboards with RAG indicators
- One-click PDF generation for board meetings
- Automated stakeholder communications

---

## Skills Demonstrated

- **Governance, Risk & Compliance (GRC)** — risk register design, escalation frameworks, compliance scoring
- **Cyber Security Assurance** — ISO 27001 mapping, control effectiveness, remediation tracking
- **Python Engineering** — modular architecture, clean code, type hints, docstrings, dataclasses
- **Data Engineering** — SQLite databases, snapshot history, delta analysis
- **Data Visualisation** — interactive Plotly charts, heatmaps, theme-aware styling
- **Automation** — Outlook COM integration, PDF generation, bulk workflows
- **Security Engineering** — zero-credential design, input validation, audit trails
- **Software Architecture** — separation of concerns, 10+ utility modules, package design
- **UX Design** — dark mode, proactive alerts, executive-focused layouts
- **Version Control** — semantic versioning, iterative releases, clean Git workflow

---

## Resume Statement

> Designed and engineered a production-grade GRC compliance dashboard using Python, Streamlit, and Plotly — delivering real-time risk posture visibility, quantitative risk scoring, intelligent threshold alerting, ISO 27001 control coverage, and secure Outlook email dispatch. Implemented SQLite-backed risk history with daily snapshots, a full governance audit trail, and a modular architecture across 10+ utility modules. Features dark/light theming, multi-page PDF management reports, and automated bulk communications — all built with a zero-credential security model across 9 iterative releases.

---

## Author

**Taiwo Durodola-Tunde**
Cyber Security Governance & Assurance

---

## License

This project is licensed under the MIT License.
