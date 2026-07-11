"""
GRC Compliance Dashboard - Utility Modules
Version: 2.4.0

Package Structure:
    config.py          - Centralised environment-based configuration
    auth.py            - Authentication & session management
    data_loader.py     - CSV loading, validation, caching
    metrics.py         - Compliance scoring, escalation, summaries
    charts.py          - Plotly chart generation
    pdf_generator.py   - PDF report generation (legacy + enhanced)
    email_dispatcher.py - Multi-provider email dispatch
    risk_scoring.py    - Quantitative risk scoring engine
    database.py        - SQLite history, snapshots, multi-org schema
    audit_trail.py     - Action logging for governance evidence
    alerts.py          - Threshold detection & notifications
    theme.py           - Light/dark mode theming
    jira_integration.py - Jira REST API risk-to-issue sync
"""

from .data_loader import (
    load_risk_register,
    load_controls,
    load_compliance_history,
    load_all_data,
    validate_dataframe,
    RISK_REGISTER_REQUIRED_COLUMNS,
)

from .metrics import (
    calculate_compliance_score,
    calculate_risk_metrics,
    calculate_escalation,
    determine_health_rating,
    generate_monthly_summary,
)

from .charts import (
    create_compliance_trend_chart,
    create_control_pie_chart,
    create_risk_bar_chart,
    create_risk_status_pie,
    create_heatmap,
    create_escalation_bar_chart,
    create_overdue_timeline,
    create_management_trend_chart,
    create_score_distribution_chart,
    create_score_waterfall_chart,
)

from .pdf_generator import (
    generate_pdf,
    generate_enhanced_pdf,
    set_version,
)

from .email_dispatcher import OutlookDispatcher

from .risk_scoring import (
    calculate_risk_scores,
    get_top_risks,
    get_score_band,
    get_score_distribution,
)

from .database import (
    init_database,
    capture_snapshot,
    get_snapshots,
    get_snapshot_detail,
    get_risk_history,
    get_latest_delta,
    has_snapshot_today,
    get_snapshot_count,
)

from .audit_trail import (
    init_audit_table,
    log_action,
    get_audit_trail,
    get_audit_summary,
    get_recent_actions,
    get_audit_count,
    export_audit_trail,
    get_today_actions,
    VALID_ACTIONS,
)

from .alerts import (
    evaluate_alerts,
    get_alert_config,
    AlertConfig,
    Alert,
)

from .theme import (
    get_theme,
    apply_chart_theme,
    get_available_themes,
    get_custom_css,
)

from .cloud_auth import check_password

from .db_manager import db as database_manager
from .db_postgres import is_postgres_available

from .csv_validator import validate_uploaded_csv
from .logger import get_logger

from .jira_integration import (
    JiraClient,
    JiraConfig,
    JiraIssueResult,
    build_jira_client_from_config,
    summarise_push_results,
)

from .config import config, AppConfig

from .auth import (
    require_auth,
    get_current_user,
    show_logout_button,
    create_credentials_file,
    is_admin,
)

from .database import (
    init_database,
    capture_snapshot,
    get_snapshots,
    get_snapshot_detail,
    get_risk_history,
    get_latest_delta,
    has_snapshot_today,
    get_snapshot_count,
    get_or_create_org,
    list_organisations,
)
