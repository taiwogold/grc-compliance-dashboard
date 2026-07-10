"""
GRC Compliance Dashboard - Utility Modules
Version: 2.1.1

Package Structure:
    data_loader.py     - CSV loading, validation, caching
    metrics.py         - Compliance scoring, escalation, summaries
    charts.py          - Plotly chart generation
    pdf_generator.py   - PDF report generation (legacy + enhanced)
    email_dispatcher.py - Secure Outlook COM email dispatch
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
)

from .pdf_generator import (
    generate_pdf,
    generate_enhanced_pdf,
    set_version,
)

from .email_dispatcher import OutlookDispatcher
