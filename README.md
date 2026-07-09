# 🛡️ GRC Compliance Dashboard

An interactive Governance, Risk & Compliance (GRC) dashboard built with Python, Streamlit and Plotly to visualize risk posture, compliance metrics, control effectiveness, and remediation progress.

The dashboard simulates the type of reporting used by Cyber Security Governance & Assurance teams to provide leadership visibility into risk management, control implementation, compliance status and remediation activities.

---

## Overview

This project was created to demonstrate how risk and compliance data can be transformed into meaningful executive reporting through interactive dashboards and automation.

The application enables stakeholders to:

- Monitor compliance performance
- Track open and closed risks
- Visualize risk exposure
- Assess ISO 27001 control coverage
- Review remediation progress
- Generate management-ready metrics

---

## Current Features (Phase 1 – MVP)

### Risk Register Management

- CSV-based risk register
- Risk status tracking
- Risk severity categorization
- Risk owner assignment

### Executive KPI Dashboard

- High Risk Count
- Open Risk Count
- Closed Risk Count
- Implemented Controls
- Compliance Score

### Interactive Reporting

- Risk Distribution Charts
- Control Implementation Charts
- Open vs Closed Actions Tracking
- Executive Summary Metrics
- Interactive Risk Table

### Data Management

- CSV Import
- Data Filtering
- Dynamic Dashboard Updates

---

## Phase 2 – Professional Dashboard

The next stage focuses on aligning the dashboard with capabilities commonly found in enterprise Governance, Risk & Compliance tooling.

### Planned Features

✅ Compliance Score

✅ Risk Heat Map

✅ Open vs Closed Actions

✅ Risk Owner Filters

✅ Executive Summary Dashboard

✅ ISO 27001 Control Coverage

✅ Enhanced Visual Analytics

These enhancements provide leadership-focused reporting and better visibility into organizational risk posture.

---

## Phase 3 – Automation

The automation phase introduces workflow capabilities often performed manually by Governance and Assurance teams.

### Planned Features

✅ Risk Owner Reminder Generation

✅ Outlook Email Integration

✅ Reminder Scheduling

✅ Overdue Risk Escalation

✅ Management Summary Generation

✅ PDF Report Export

✅ Monthly Compliance Reporting

The goal is to reduce manual administration effort while improving stakeholder engagement and accountability.

---

## Phase 4 – Enterprise Features

This phase simulates capabilities found in commercial GRC platforms and large enterprise governance environments.

### Planned Features

✅ User Authentication

✅ SQL Database Backend

✅ Risk History Tracking

✅ Audit Trail Logging

✅ Power BI Integration

✅ Microsoft Graph Integration

✅ Role-Based Access Control

✅ Vulnerability Data Ingestion

✅ Compliance Trend Analysis

✅ Multi-Department Reporting

---

## Technology Stack

### Front End

- Streamlit

### Data Processing

- Pandas

### Data Visualisation

- Plotly

### Reporting

- Streamlit
- CSV
- PDF Export (Planned)

### Automation

- Microsoft Graph API (Planned)
- Outlook Integration (Planned)

### Version Control

- Git
- GitHub

---

## Project Structure

```text
grc-compliance-dashboard/
│
├── data/
│   ├── risk_register.csv
│   └── control_matrix.csv
│
├── screenshots/
│
├── dashboard.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR-USERNAME/grc-compliance-dashboard.git
```

Navigate to the project:

```bash
cd grc-compliance-dashboard
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment:

### Windows

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Running the Dashboard

Launch Streamlit:

```bash
streamlit run dashboard.py
```

Open:

```text
http://localhost:8501
```

---

## Example Use Cases

### Governance & Assurance

- Risk reporting
- Control effectiveness monitoring
- Compliance status reviews

### Security Risk Management

- Vulnerability trend analysis
- Risk heat mapping
- Remediation tracking

### Audit & Compliance

- ISO 27001 reporting
- Audit action tracking
- Compliance score measurement

### Leadership Reporting

- Executive dashboards
- Board reporting packs
- Compliance performance monitoring

---

## Skills Demonstrated

This project demonstrates practical capabilities in:

- Governance, Risk & Compliance (GRC)
- Cyber Security Assurance
- Data Visualisation
- Risk Reporting
- Metrics & KPI Development
- Python Development
- Dashboard Design
- Automation Engineering
- Version Control
- GitHub Portfolio Development

---

## Future Roadmap

### v1.0
✅ Initial Dashboard

### v1.1
✅ Compliance Score
✅ Executive Summary
✅ ISO 27001 Coverage

### v1.2
⬜ Risk Owner Filter
⬜ Risk Heat Map
⬜ Open vs Closed Actions

### v2.0
⬜ Email Automation
⬜ Escalation Tracking
⬜ PDF Reports

### v3.0
⬜ Microsoft Graph
⬜ SQL Database
⬜ Authentication

---

## Resume Statement

Built an interactive GRC compliance dashboard using Python, Streamlit and Plotly to visualize risk exposure, compliance metrics, ISO 27001 control coverage, remediation progress and executive-level cybersecurity reporting. Implemented automated reporting capabilities and designed a scalable architecture for future enterprise integration.
