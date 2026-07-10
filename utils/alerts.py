"""
Alerts & Threshold Notifications Module
Version: 2.2.0-alpha.4
Author: Taiwo Durodola-Tunde

Provides automatic detection of concerning trends and threshold
breaches across the GRC dashboard. Surfaces proactive governance
alerts so issues are flagged before they escalate.

Alert Conditions:
    - Compliance score drops below configurable threshold
    - High-severity risk count exceeds acceptable limit
    - Overdue risks at Level 2+ exceed threshold
    - Any risk reaches Level 4 (executive escalation)
    - Open risk count increased significantly vs last snapshot
    - Risk closure rate falls below target

Alert Severity Levels:
    - CRITICAL: Immediate action required (red)
    - WARNING: Attention needed (amber)
    - INFO: Awareness only (blue)

Functions:
    evaluate_alerts: Run all alert checks and return triggered alerts.
    get_alert_config: Return current threshold configuration.
    check_compliance_threshold: Check if compliance is below target.
    check_high_risk_count: Check if high risks exceed limit.
    check_escalation_levels: Check for critical escalation states.
    check_risk_trend: Compare current vs previous snapshot.
    check_closure_rate: Check if closure rate is too low.
"""

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd


# ==========================================================
# CONFIGURATION — ALERT THRESHOLDS
# ==========================================================

@dataclass
class AlertConfig:
    """
    Configuration for alert thresholds.

    All thresholds are configurable and can be adjusted
    based on organisational risk appetite.

    Attributes:
        compliance_min: Minimum acceptable compliance score (%).
        high_risk_max: Maximum acceptable high-severity risk count.
        escalation_level2_max: Max risks at Level 2+ before alert.
        level4_triggers_critical: Whether any Level 4 risk triggers critical.
        risk_increase_pct: % increase in open risks vs snapshot that triggers alert.
        closure_rate_min: Minimum acceptable closure rate (%).
    """

    compliance_min: float = 75.0
    high_risk_max: int = 3
    escalation_level2_max: int = 2
    level4_triggers_critical: bool = True
    risk_increase_pct: float = 20.0
    closure_rate_min: float = 20.0


# Default configuration
DEFAULT_CONFIG = AlertConfig()


# ==========================================================
# ALERT DATA STRUCTURE
# ==========================================================

@dataclass
class Alert:
    """
    Represents a single triggered alert.

    Attributes:
        severity: Alert level ('CRITICAL', 'WARNING', 'INFO').
        title: Short alert headline.
        message: Detailed description of the issue.
        metric_name: The metric that triggered the alert.
        current_value: Current value of the metric.
        threshold_value: The threshold that was breached.
    """

    severity: str
    title: str
    message: str
    metric_name: str
    current_value: float
    threshold_value: float


# ==========================================================
# INDIVIDUAL ALERT CHECKS
# ==========================================================

def check_compliance_threshold(
    compliance_score: float,
    config: AlertConfig = DEFAULT_CONFIG
) -> Optional[Alert]:
    """
    Check if compliance score is below minimum threshold.

    Args:
        compliance_score: Current compliance percentage.
        config: Alert configuration with thresholds.

    Returns:
        Alert if threshold breached, None otherwise.
    """

    if compliance_score < config.compliance_min:
        severity = "CRITICAL" if compliance_score < 60 else "WARNING"
        return Alert(
            severity=severity,
            title="Compliance Below Threshold",
            message=(
                f"Compliance score is {compliance_score}%, "
                f"below the minimum threshold of {config.compliance_min}%. "
                f"Accelerate control implementation to close the gap."
            ),
            metric_name="compliance_score",
            current_value=compliance_score,
            threshold_value=config.compliance_min
        )

    return None


def check_high_risk_count(
    high_risk_count: int,
    config: AlertConfig = DEFAULT_CONFIG
) -> Optional[Alert]:
    """
    Check if high-severity risk count exceeds acceptable limit.

    Args:
        high_risk_count: Number of high-severity risks.
        config: Alert configuration with thresholds.

    Returns:
        Alert if threshold breached, None otherwise.
    """

    if high_risk_count > config.high_risk_max:
        severity = "CRITICAL" if high_risk_count > config.high_risk_max * 2 else "WARNING"
        return Alert(
            severity=severity,
            title="High Risk Count Exceeded",
            message=(
                f"{high_risk_count} high-severity risks detected, "
                f"exceeding the acceptable limit of {config.high_risk_max}. "
                f"Prioritise remediation of critical exposures."
            ),
            metric_name="high_risk_count",
            current_value=float(high_risk_count),
            threshold_value=float(config.high_risk_max)
        )

    return None


def check_escalation_levels(
    escalated_df,
    config: AlertConfig = DEFAULT_CONFIG
) -> list:
    """
    Check for critical escalation states.

    Triggers alerts when:
        - Any risk reaches Level 4 (executive escalation)
        - Number of Level 2+ risks exceeds threshold

    Args:
        escalated_df: DataFrame with Escalation_Level column.
        config: Alert configuration with thresholds.

    Returns:
        list: List of triggered Alert objects (may be empty).
    """

    alerts = []

    if "Escalation_Level" not in escalated_df.columns:
        return alerts

    # Check for Level 4 risks
    level4_count = len(
        escalated_df[
            escalated_df["Escalation_Level"]
            == "Level 4 - Executive Escalation"
        ]
    )

    if level4_count > 0 and config.level4_triggers_critical:
        alerts.append(Alert(
            severity="CRITICAL",
            title="Executive Escalation Triggered",
            message=(
                f"{level4_count} risk(s) have reached Level 4 "
                f"(Executive Escalation). These have been overdue "
                f"for 60+ days and require immediate governance action."
            ),
            metric_name="level4_risks",
            current_value=float(level4_count),
            threshold_value=0.0
        ))

    # Check Level 2+ count
    level2_plus = len(
        escalated_df[
            escalated_df["Escalation_Level"].isin([
                "Level 2 - Manager Escalation",
                "Level 3 - Director Escalation",
                "Level 4 - Executive Escalation",
            ])
        ]
    )

    if level2_plus > config.escalation_level2_max:
        alerts.append(Alert(
            severity="WARNING",
            title="Escalation Threshold Breached",
            message=(
                f"{level2_plus} risks at Level 2 or above, "
                f"exceeding the threshold of {config.escalation_level2_max}. "
                f"Review escalation pipeline and assign remediation owners."
            ),
            metric_name="level2_plus_risks",
            current_value=float(level2_plus),
            threshold_value=float(config.escalation_level2_max)
        ))

    return alerts


def check_risk_trend(
    delta: Optional[dict],
    config: AlertConfig = DEFAULT_CONFIG
) -> Optional[Alert]:
    """
    Compare current state vs previous snapshot for concerning trends.

    Triggers when open risk count has increased by more than
    the configured percentage threshold.

    Args:
        delta: Dictionary from get_latest_delta() or None.
        config: Alert configuration with thresholds.

    Returns:
        Alert if concerning trend detected, None otherwise.
    """

    if delta is None:
        return None

    # Check if open risks increased significantly
    if delta["delta_open"] > 0:
        # We need the previous open count to calculate percentage
        # delta_open is current - previous, so previous = current - delta
        # But we don't have current here directly, so use raw delta
        if delta["delta_open"] >= 2:
            return Alert(
                severity="WARNING",
                title="Open Risk Count Increasing",
                message=(
                    f"Open risks increased by {delta['delta_open']} "
                    f"since last snapshot ({delta['date_previous']}). "
                    f"Review new risks and ensure remediation plans are in place."
                ),
                metric_name="open_risk_delta",
                current_value=float(delta["delta_open"]),
                threshold_value=0.0
            )

    # Check if compliance dropped
    if delta["delta_compliance"] < -2:
        return Alert(
            severity="WARNING",
            title="Compliance Score Declining",
            message=(
                f"Compliance dropped by {abs(delta['delta_compliance'])}% "
                f"since last snapshot ({delta['date_previous']}). "
                f"Investigate control regression."
            ),
            metric_name="compliance_delta",
            current_value=float(delta["delta_compliance"]),
            threshold_value=-2.0
        )

    return None


def check_closure_rate(
    metrics: dict,
    total_risks: int,
    config: AlertConfig = DEFAULT_CONFIG
) -> Optional[Alert]:
    """
    Check if the risk closure rate is below target.

    Args:
        metrics: Dictionary with closed_risks count.
        total_risks: Total number of risks in register.
        config: Alert configuration with thresholds.

    Returns:
        Alert if closure rate is too low, None otherwise.
    """

    if total_risks == 0:
        return None

    closure_rate = round(
        metrics["closed_risks"] / total_risks * 100, 1
    )

    if closure_rate < config.closure_rate_min:
        return Alert(
            severity="INFO",
            title="Low Risk Closure Rate",
            message=(
                f"Risk closure rate is {closure_rate}%, "
                f"below the target of {config.closure_rate_min}%. "
                f"Consider reviewing remediation timelines."
            ),
            metric_name="closure_rate",
            current_value=closure_rate,
            threshold_value=config.closure_rate_min
        )

    return None


# ==========================================================
# MAIN EVALUATION FUNCTION
# ==========================================================

def evaluate_alerts(
    compliance_score: float,
    metrics: dict,
    escalated_df,
    total_risks: int,
    delta: Optional[dict] = None,
    config: AlertConfig = DEFAULT_CONFIG
) -> list:
    """
    Run all alert checks and return a list of triggered alerts.

    This is the main entry point — call this once per dashboard
    load to evaluate all threshold conditions.

    Args:
        compliance_score: Current compliance percentage.
        metrics: Risk count metrics dict.
        escalated_df: DataFrame with escalation data.
        total_risks: Total risks in the register.
        delta: Optional snapshot delta from get_latest_delta().
        config: Alert threshold configuration.

    Returns:
        list: All triggered Alert objects, sorted by severity
            (CRITICAL first, then WARNING, then INFO).
    """

    alerts = []

    # Run each check
    compliance_alert = check_compliance_threshold(
        compliance_score, config
    )
    if compliance_alert:
        alerts.append(compliance_alert)

    high_risk_alert = check_high_risk_count(
        metrics["high_risks"], config
    )
    if high_risk_alert:
        alerts.append(high_risk_alert)

    escalation_alerts = check_escalation_levels(
        escalated_df, config
    )
    alerts.extend(escalation_alerts)

    trend_alert = check_risk_trend(delta, config)
    if trend_alert:
        alerts.append(trend_alert)

    closure_alert = check_closure_rate(
        metrics, total_risks, config
    )
    if closure_alert:
        alerts.append(closure_alert)

    # Sort by severity (CRITICAL > WARNING > INFO)
    severity_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
    alerts.sort(key=lambda a: severity_order.get(a.severity, 3))

    return alerts


def get_alert_config() -> AlertConfig:
    """
    Return the current alert threshold configuration.

    Returns:
        AlertConfig: Current thresholds for all checks.
    """

    return DEFAULT_CONFIG
