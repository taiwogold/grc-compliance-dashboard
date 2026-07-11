"""
GRC Compliance Dashboard - FastAPI REST API
Version: 3.2.0
Author: Taiwo Durodola-Tunde

Provides RESTful API endpoints for programmatic access to
GRC data. Enables integrations with Power BI, Teams webhooks,
SIEM tools, and custom automation scripts.

Endpoints:
    GET  /api/v1/health          - Health check (no auth)
    GET  /api/v1/risks           - Get all risks
    GET  /api/v1/risks/{risk_id} - Get specific risk
    GET  /api/v1/compliance      - Get compliance score & metrics
    GET  /api/v1/controls        - Get control status
    GET  /api/v1/escalations     - Get overdue/escalated risks
    GET  /api/v1/scores          - Get risk scores
    GET  /api/v1/snapshots       - Get historical snapshots
    GET  /api/v1/audit           - Get audit trail entries

Running Standalone:
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

Security:
    All endpoints (except /health) require X-API-Key header.
    Keys are configured via environment variables or st.secrets.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .auth import get_api_key

logger = logging.getLogger(__name__)


# ==========================================================
# APP CONFIGURATION
# ==========================================================

app = FastAPI(
    title="GRC Compliance Dashboard API",
    description=(
        "RESTful API for Governance, Risk & Compliance data. "
        "Provides programmatic access to risk register, compliance "
        "metrics, control status, and audit trail."
    ),
    version="3.2.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS — allow all origins for development
# Restrict in production via environment variable
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ==========================================================
# HELPER: LOAD DATA
# ==========================================================

def _load_risk_register():
    """Load risk register from CSV."""
    import pandas as pd
    try:
        df = pd.read_csv("data/risk_register.csv")
        if "Owner_Email" not in df.columns:
            df["Owner_Email"] = ""
        return df
    except Exception as e:
        logger.error(f"Failed to load risk register: {e}")
        return None


def _load_controls():
    """Load controls from CSV."""
    import pandas as pd
    try:
        return pd.read_csv("data/controls.csv")
    except Exception as e:
        logger.error(f"Failed to load controls: {e}")
        return None


# ==========================================================
# ENDPOINTS
# ==========================================================

@app.get("/api/v1/health")
async def health_check():
    """
    Health check endpoint — no authentication required.

    Returns:
        dict: API status and version info.
    """
    return {
        "status": "healthy",
        "version": "3.2.0",
        "timestamp": datetime.now().isoformat(),
        "service": "GRC Compliance Dashboard API",
    }


@app.get("/api/v1/risks")
async def get_risks(
    status: Optional[str] = Query(None, description="Filter by status (Open/Closed)"),
    level: Optional[str] = Query(None, description="Filter by risk level (High/Medium/Low)"),
    owner: Optional[str] = Query(None, description="Filter by risk owner"),
    api_key: str = Depends(get_api_key)
):
    """
    Get all risks from the risk register.

    Supports filtering by status, level, and owner.

    Returns:
        dict: List of risk records with metadata.
    """
    df = _load_risk_register()
    if df is None:
        raise HTTPException(status_code=500, detail="Failed to load risk data")

    # Apply filters
    if status:
        df = df[df["Status"].str.lower() == status.lower()]
    if level:
        df = df[df["Risk_Level"].str.lower() == level.lower()]
    if owner:
        df = df[df["Risk_Owner"].str.lower().str.contains(owner.lower())]

    return {
        "count": len(df),
        "filters_applied": {
            "status": status,
            "level": level,
            "owner": owner,
        },
        "risks": df.to_dict("records"),
    }


@app.get("/api/v1/risks/{risk_id}")
async def get_risk_by_id(
    risk_id: str,
    api_key: str = Depends(get_api_key)
):
    """
    Get a specific risk by its ID.

    Args:
        risk_id: The Risk_ID to look up (e.g. 'R001').

    Returns:
        dict: Single risk record or 404.
    """
    df = _load_risk_register()
    if df is None:
        raise HTTPException(status_code=500, detail="Failed to load risk data")

    risk = df[df["Risk_ID"] == risk_id.upper()]

    if risk.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Risk {risk_id} not found"
        )

    return {
        "risk": risk.iloc[0].to_dict()
    }


@app.get("/api/v1/compliance")
async def get_compliance(
    api_key: str = Depends(get_api_key)
):
    """
    Get current compliance score and health metrics.

    Returns:
        dict: Compliance score, rating, and control breakdown.
    """
    controls_df = _load_controls()
    risk_df = _load_risk_register()

    if controls_df is None or risk_df is None:
        raise HTTPException(status_code=500, detail="Failed to load data")

    total = len(controls_df)
    implemented = len(controls_df[controls_df["Status"] == "Implemented"])
    score = round((implemented / total) * 100, 1) if total > 0 else 0

    # Health rating
    if score >= 80:
        rating = "Healthy"
    elif score >= 60:
        rating = "Requires Attention"
    else:
        rating = "Critical"

    return {
        "compliance_score": score,
        "health_rating": rating,
        "controls": {
            "total": total,
            "implemented": implemented,
            "in_progress": len(controls_df[controls_df["Status"] == "In Progress"]),
            "planned": len(controls_df[controls_df["Status"] == "Planned"]),
        },
        "risks": {
            "total": len(risk_df),
            "open": len(risk_df[risk_df["Status"] == "Open"]),
            "closed": len(risk_df[risk_df["Status"] == "Closed"]),
            "high": len(risk_df[risk_df["Risk_Level"] == "High"]),
        },
    }


@app.get("/api/v1/controls")
async def get_controls(
    status: Optional[str] = Query(None, description="Filter by status"),
    api_key: str = Depends(get_api_key)
):
    """
    Get ISO 27001 control implementation status.

    Returns:
        dict: Control records with optional status filter.
    """
    df = _load_controls()
    if df is None:
        raise HTTPException(status_code=500, detail="Failed to load controls")

    if status:
        df = df[df["Status"].str.lower() == status.lower()]

    return {
        "count": len(df),
        "controls": df.to_dict("records"),
    }


@app.get("/api/v1/escalations")
async def get_escalations(
    api_key: str = Depends(get_api_key)
):
    """
    Get all overdue and escalated risks.

    Returns:
        dict: Escalated risks with days overdue and levels.
    """
    import pandas as pd
    from datetime import date

    df = _load_risk_register()
    if df is None:
        raise HTTPException(status_code=500, detail="Failed to load risk data")

    # Parse due dates and calculate overdue
    if "Due_Date" in df.columns:
        df["Due_Date"] = pd.to_datetime(df["Due_Date"], errors="coerce")
        today = pd.Timestamp(date.today())
        df["Days_Overdue"] = (today - df["Due_Date"]).dt.days.clip(lower=0)
        df.loc[df["Status"] == "Closed", "Days_Overdue"] = 0
    else:
        df["Days_Overdue"] = 0

    # Filter to overdue open risks only
    overdue = df[(df["Days_Overdue"] > 0) & (df["Status"] == "Open")].copy()

    # Assign escalation levels
    def _get_level(days):
        if days > 60:
            return "Level 4 - Executive Escalation"
        elif days > 30:
            return "Level 3 - Director Escalation"
        elif days > 14:
            return "Level 2 - Manager Escalation"
        else:
            return "Level 1 - Owner Reminder"

    overdue["Escalation_Level"] = overdue["Days_Overdue"].apply(_get_level)

    # Format for JSON response
    overdue["Due_Date"] = overdue["Due_Date"].dt.strftime("%Y-%m-%d")

    return {
        "total_overdue": len(overdue),
        "escalations": overdue[[
            "Risk_ID", "Risk_Name", "Risk_Level", "Risk_Owner",
            "Due_Date", "Days_Overdue", "Escalation_Level"
        ]].to_dict("records"),
    }


@app.get("/api/v1/scores")
async def get_risk_scores(
    top_n: int = Query(10, description="Number of top risks to return"),
    api_key: str = Depends(get_api_key)
):
    """
    Get quantitative risk scores for all risks.

    Returns:
        dict: Scored risks with residual scores and bands.
    """
    import sys
    sys.path.insert(0, ".")

    from utils.risk_scoring import calculate_risk_scores, get_score_distribution

    df = _load_risk_register()
    if df is None:
        raise HTTPException(status_code=500, detail="Failed to load risk data")

    scored = calculate_risk_scores(df)
    distribution = get_score_distribution(scored)

    top_risks = (
        scored.nlargest(top_n, "Residual_Risk_Score")
        [["Risk_ID", "Risk_Name", "Risk_Owner", "Risk_Level",
          "Base_Score", "Overdue_Modifier", "Control_Modifier",
          "Residual_Risk_Score", "Score_Band"]]
        .to_dict("records")
    )

    return {
        "distribution": distribution,
        "top_risks": top_risks,
        "total_scored": len(scored),
    }


@app.get("/api/v1/snapshots")
async def get_snapshots(
    limit: int = Query(30, description="Max snapshots to return"),
    api_key: str = Depends(get_api_key)
):
    """
    Get historical risk snapshots.

    Returns:
        dict: Snapshot summaries ordered by date descending.
    """
    import sys
    sys.path.insert(0, ".")

    try:
        from utils.database import get_snapshots as db_get_snapshots
        snapshots_df = db_get_snapshots()

        if snapshots_df.empty:
            return {"count": 0, "snapshots": []}

        snapshots_df = snapshots_df.head(limit)

        return {
            "count": len(snapshots_df),
            "snapshots": snapshots_df.to_dict("records"),
        }

    except Exception as e:
        return {
            "count": 0,
            "snapshots": [],
            "note": "Snapshot history not available",
        }


@app.get("/api/v1/audit")
async def get_audit_trail(
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    limit: int = Query(50, description="Max entries to return"),
    api_key: str = Depends(get_api_key)
):
    """
    Get audit trail entries.

    Returns:
        dict: Audit log entries ordered by timestamp descending.
    """
    import sys
    sys.path.insert(0, ".")

    try:
        from utils.audit_trail import get_audit_trail as db_get_audit

        audit_df = db_get_audit(
            action_type=action_type,
            limit=limit
        )

        if audit_df.empty:
            return {"count": 0, "entries": []}

        return {
            "count": len(audit_df),
            "entries": audit_df.to_dict("records"),
        }

    except Exception as e:
        return {
            "count": 0,
            "entries": [],
            "note": "Audit trail not available",
        }
