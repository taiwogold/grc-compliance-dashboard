# 🛡️ GRC Compliance Dashboard

A production-grade Governance, Risk & Compliance dashboard built with Python, Streamlit and Plotly. Delivers real-time visibility into risk posture, compliance metrics, ISO 27001 control effectiveness, escalation tracking, and automated remediation workflows.

Designed for Cyber Security Governance & Assurance teams to provide executive-level reporting, reduce manual administration, and drive accountability across risk owners.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.59-red?logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-6.8-purple?logo=plotly&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-2.1.1-orange)

---

## Overview

This project transforms raw risk and compliance data into actionable executive reporting through interactive dashboards, automated email dispatch, and professional PDF management reports.

**What it enables:**

- Real-time compliance posture monitoring with RAG health rating
- Risk register management with severity categorisation and owner tracking
- Automated overdue risk escalation with tiered severity levels
- One-click Outlook email dispatch to risk owners (zero stored credentials)
- Multi-page PDF management reports with sign-off sections
- Month-over-month trend analysis with target threshold tracking
- ISO 27001 control coverage visualisation

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
│   └── email_dispatcher.py      # Secure Outlook COM integration
│
├── data/
│   ├── risk_register.csv        # Risk register source data
│   ├── controls.csv             # ISO 27001 control matrix
│   └── compliance_history.csv   # Monthly compliance scores
│
├── logs/
│   └── email_audit.csv          # Email dispatch audit trail
│
├── assets/
│   └── banner.png               # Optional dashboard banner
│
├── requirements.txt
├── .gitignore
└── README.md
```

The application follows a **modular architecture** — `dashboard.py` is a thin orchestration layer (~480 lines) that imports all business logic from purpose-built utility modules. Each module is independently testable and maintainable.

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
| **Audit Trail** | Every dispatch logged to `logs/email_audit.csv` |
| **Input Validation** | Email format checks, injection prevention |
| **Confirmation Required** | Checkbox + button before any dispatch |

---

## Security Design

The email integration was built with a security-first mindset:

| Control | Implementation |
|---------|---------------|
| No stored credentials | COM uses existing authenticated Outlook session |
| Corporate routing | All emails go via Exchange (DLP, retention, audit) |
| Rate limiting | Session-based cap prevents accidental mass-mailing |
| Input validation | Email format validation, injection char blocking |
| Content sanitisation | Null byte removal, dangerous character filtering |
| Audit logging | Timestamped CSV log of every dispatch attempt |
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

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Streamlit |
| **Data Processing** | Pandas, NumPy |
| **Visualisation** | Plotly Express, Plotly Graph Objects |
| **PDF Generation** | ReportLab (SimpleDocTemplate, Tables, Styles) |
| **Email Dispatch** | pywin32 (Outlook COM automation) |
| **Version Control** | Git, GitHub |

---

## Version History

| Version | Release | Features |
|---------|---------|----------|
| **v2.1.1** | Current | Modular refactor — extracted utils package |
| **v2.1.0** | ✅ | Outlook integration, automated reminder dispatch |
| **v2.0.2** | ✅ | Monthly management reports, enhanced PDF exports |
| **v2.0.1** | ✅ | Overdue risk escalation tracking, due date logic |
| **v2.0.0** | ✅ | Professional dashboard with heat maps, filters, ISO coverage |
| **v1.1.0** | ✅ | Compliance score, executive summary |
| **v1.0.0** | ✅ | Initial MVP dashboard |

---

## Roadmap

### v2.2.0 — Planned

- [ ] Microsoft Teams webhook notifications
- [ ] Risk history tracking (point-in-time snapshots)
- [ ] Configurable escalation thresholds
- [ ] Dashboard theming (dark/light mode)

### v3.0.0 — Enterprise

- [ ] User authentication (Azure AD / SSO)
- [ ] SQL database backend (SQLite → PostgreSQL)
- [ ] Role-based access control (RBAC)
- [ ] Full audit trail with user attribution
- [ ] Power BI integration
- [ ] Microsoft Graph API for email
- [ ] Vulnerability data ingestion
- [ ] Multi-department reporting
- [ ] Compliance framework selector (ISO 27001, NIST, CIS)

---

## Use Cases

**Governance & Assurance**
- Monthly risk reporting to governance committees
- Control effectiveness monitoring
- Compliance status reviews and board packs

**Security Risk Management**
- Risk heat mapping for prioritisation
- Remediation tracking and escalation
- Trend analysis for emerging threats

**Audit & Compliance**
- ISO 27001 control coverage reporting
- Audit action tracking with due dates
- Compliance score measurement over time

**Leadership Reporting**
- Executive dashboards with RAG indicators
- One-click PDF generation for board meetings
- Automated stakeholder communications

---

## Skills Demonstrated

- **Governance, Risk & Compliance (GRC)** — risk register design, escalation frameworks, compliance scoring
- **Cyber Security Assurance** — ISO 27001 mapping, control effectiveness, remediation tracking
- **Python Engineering** — modular architecture, clean code, type hints, docstrings
- **Data Visualisation** — interactive Plotly charts, heatmaps, trend analysis
- **Automation** — Outlook COM integration, PDF generation, bulk workflows
- **Security Engineering** — zero-credential design, input validation, audit trails
- **Software Architecture** — separation of concerns, utility modules, package design
- **Version Control** — semantic versioning, iterative releases, Git workflow

---

## Resume Statement

> Designed and engineered a production-grade GRC compliance dashboard using Python, Streamlit, and Plotly — delivering real-time risk posture visibility, ISO 27001 control coverage, automated overdue escalation tracking, and secure Outlook email dispatch to risk owners. Implemented a modular architecture with professional PDF management reporting, month-over-month trend analysis, and a security-first email integration requiring zero stored credentials. Built iteratively across 7 releases using semantic versioning and clean separation of concerns.

---

## Author

**Taiwo Durodola-Tunde**
Cyber Security Governance & Assurance

---

## License

This project is licensed under the MIT License.
