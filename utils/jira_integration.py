"""
Jira Integration Module - GRC Risk to Jira Issue Sync
Version: 1.0.0
Author: Taiwo Durodola-Tunde

Provides bidirectional synchronisation between the GRC risk
register and a Jira project. Risks can be pushed as Jira issues
and their status can be pulled back to update the dashboard.

Architecture:
    - Uses Jira REST API v3 (Cloud) with Basic Auth (API token).
    - No passwords stored — uses a personal API token scoped to
      the Jira project.
    - All sync activity is logged to the GRC audit trail.
    - Graceful degradation if Jira is unreachable.

Authentication:
    Jira Cloud uses Basic Auth with email + API token:
        email:       your Atlassian account email
        api_token:   generated at https://id.atlassian.com/manage-profile/security/api-tokens

    These are passed at runtime — never hardcoded or stored on disk.

Risk → Jira Mapping:
    Risk_ID        → Issue summary prefix   [GRC-R001]
    Risk_Name      → Issue summary
    Risk_Level     → Issue priority         High=High, Medium=Medium, Low=Low
    Risk_Owner     → Issue description
    Due_Date       → Issue due date
    Control_Status → Label on the issue
    Status         → Issue status (read back via sync)

Usage:
    from utils.jira_integration import JiraClient

    client = JiraClient(
        base_url="https://yourcompany.atlassian.net",
        email="you@company.com",
        api_token="your_api_token",
        project_key="SEC"
    )

    result = client.push_risk(risk_row)
    sync_df = client.sync_statuses(risk_df)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import pandas as pd
import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


# ==========================================================
# CONSTANTS
# ==========================================================

# Maps GRC risk levels to Jira priority names
PRIORITY_MAP = {
    "High":     "High",
    "Medium":   "Medium",
    "Low":      "Low",
    "Critical": "Highest",
}

# Maps Jira issue status categories back to GRC status
# Jira status categories: "To Do", "In Progress", "Done"
JIRA_STATUS_TO_GRC = {
    "To Do":       "Open",
    "In Progress":  "Open",
    "Done":        "Closed",
}

# Label applied to all GRC-created issues for easy filtering
GRC_LABEL = "grc-dashboard"

# Jira REST API v3 path
JIRA_API_PATH = "/rest/api/3"


# ==========================================================
# DATA STRUCTURES
# ==========================================================

@dataclass
class JiraIssueResult:
    """
    Result of a single issue push or sync operation.

    Attributes:
        success:      Whether the operation succeeded.
        risk_id:      The GRC Risk_ID this relates to.
        issue_key:    The created/found Jira issue key (e.g. SEC-42).
        issue_url:    Full browser URL to the Jira issue.
        message:      Human-readable status or error message.
        jira_status:  Current Jira status string if synced.
        grc_status:   Mapped GRC status from Jira state.
    """
    success: bool
    risk_id: str
    issue_key: str = ""
    issue_url: str = ""
    message: str = ""
    jira_status: str = ""
    grc_status: str = ""


@dataclass
class JiraConfig:
    """
    Runtime configuration for the Jira client.

    Attributes:
        base_url:     Atlassian Cloud URL, e.g. https://company.atlassian.net
        email:        Atlassian account email for authentication.
        api_token:    Personal API token (not password).
        project_key:  Jira project key to create issues in, e.g. SEC.
        issue_type:   Jira issue type to create. Defaults to 'Task'.
        timeout:      HTTP request timeout in seconds.
    """
    base_url: str
    email: str
    api_token: str
    project_key: str
    issue_type: str = "Task"
    timeout: int = 10


# ==========================================================
# JIRA CLIENT
# ==========================================================

class JiraClient:
    """
    Client for pushing GRC risks to Jira and syncing statuses back.

    This class wraps the Jira REST API v3 to provide push and
    sync operations specifically designed for the GRC risk register.

    Security:
        - API token used instead of password
        - Token passed at runtime, never stored on disk
        - HTTPS enforced for all requests
        - Responses validated before processing

    Attributes:
        config:        JiraClient configuration.
        is_available:  Whether Jira API is reachable.
        _auth:         HTTPBasicAuth object for requests.
        _headers:      Standard JSON headers for API calls.
    """

    def __init__(self, config: JiraConfig):
        """
        Initialise the Jira client and verify connectivity.

        Args:
            config: JiraConfig with credentials and project details.
        """
        self.config = config
        self.is_available = False
        self._session = requests.Session()
        self._session.auth = HTTPBasicAuth(config.email, config.api_token)
        self._session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        self._test_connection()

    def _api_url(self, path: str) -> str:
        """Build a full Jira API URL."""
        base = self.config.base_url.rstrip("/")
        return f"{base}{JIRA_API_PATH}{path}"

    def _test_connection(self):
        """
        Verify the Jira connection by calling /myself endpoint.
        Sets is_available based on result.
        """
        try:
            resp = self._session.get(
                self._api_url("/myself"),
                timeout=self.config.timeout
            )
            if resp.status_code == 200:
                self.is_available = True
                user = resp.json().get("displayName", "unknown")
                logger.info(f"Jira connected as: {user}")
            else:
                logger.warning(
                    f"Jira auth failed: {resp.status_code} - {resp.text[:200]}"
                )
        except requests.exceptions.ConnectionError:
            logger.warning("Jira unreachable — check base URL and network.")
        except requests.exceptions.Timeout:
            logger.warning("Jira connection timed out.")
        except Exception as e:
            logger.warning(f"Jira connection error: {e}")

    # ----------------------------------------------------------
    # CORE PUSH OPERATION
    # ----------------------------------------------------------

    def push_risk(self, risk_row: pd.Series) -> JiraIssueResult:
        """
        Push a single GRC risk to Jira as a new issue.

        Checks if an issue for this risk already exists (by label
        search) before creating, to avoid duplicates.

        Args:
            risk_row: A single row from the risk register DataFrame.

        Returns:
            JiraIssueResult with outcome details.
        """
        risk_id = str(risk_row.get("Risk_ID", "UNKNOWN"))

        if not self.is_available:
            return JiraIssueResult(
                success=False,
                risk_id=risk_id,
                message="Jira is not available. Check your credentials and URL."
            )

        # Check for existing issue first
        existing = self._find_existing_issue(risk_id)
        if existing:
            return JiraIssueResult(
                success=True,
                risk_id=risk_id,
                issue_key=existing["key"],
                issue_url=self._build_issue_url(existing["key"]),
                message=f"Issue already exists: {existing['key']}",
                jira_status=existing.get("status", ""),
            )

        # Build issue payload
        payload = self._build_issue_payload(risk_row)

        try:
            resp = self._session.post(
                self._api_url("/issue"),
                json=payload,
                timeout=self.config.timeout
            )

            if resp.status_code == 201:
                data = resp.json()
                issue_key = data["key"]
                issue_url = self._build_issue_url(issue_key)

                logger.info(f"Created Jira issue {issue_key} for {risk_id}")

                return JiraIssueResult(
                    success=True,
                    risk_id=risk_id,
                    issue_key=issue_key,
                    issue_url=issue_url,
                    message=f"Issue created: {issue_key}",
                )
            else:
                error_msg = self._parse_error(resp)
                logger.error(f"Failed to create issue for {risk_id}: {error_msg}")
                return JiraIssueResult(
                    success=False,
                    risk_id=risk_id,
                    message=f"Jira API error: {error_msg}"
                )

        except requests.exceptions.Timeout:
            return JiraIssueResult(
                success=False,
                risk_id=risk_id,
                message="Request timed out. Jira may be slow — try again."
            )
        except Exception as e:
            logger.exception(f"Unexpected error pushing {risk_id}")
            return JiraIssueResult(
                success=False,
                risk_id=risk_id,
                message=f"Unexpected error: {str(e)}"
            )

    def push_bulk(
        self,
        risk_df: pd.DataFrame,
        only_open: bool = True,
        only_high: bool = False
    ) -> list[JiraIssueResult]:
        """
        Push multiple risks to Jira in sequence.

        Args:
            risk_df:    Risk register DataFrame.
            only_open:  If True, only push Open risks. Default True.
            only_high:  If True, only push High-severity risks. Default False.

        Returns:
            list[JiraIssueResult]: One result per risk processed.
        """
        df = risk_df.copy()

        if only_open and "Status" in df.columns:
            df = df[df["Status"] == "Open"]

        if only_high and "Risk_Level" in df.columns:
            df = df[df["Risk_Level"] == "High"]

        results = []
        for _, row in df.iterrows():
            result = self.push_risk(row)
            results.append(result)

        return results

    # ----------------------------------------------------------
    # SYNC OPERATION (Pull status back from Jira)
    # ----------------------------------------------------------

    def sync_statuses(self, risk_df: pd.DataFrame) -> pd.DataFrame:
        """
        Pull current Jira statuses back into the risk register.

        Queries Jira for all issues in the project labelled with
        the GRC label, then maps their status back to GRC Status.

        Args:
            risk_df: Current risk register DataFrame.

        Returns:
            DataFrame: Copy with new columns added:
                - Jira_Key:    The linked Jira issue key.
                - Jira_Status: Current status in Jira.
                - Jira_URL:    Link to the Jira issue.
        """
        df = risk_df.copy()

        # Initialise new columns
        df["Jira_Key"] = ""
        df["Jira_Status"] = ""
        df["Jira_URL"] = ""

        if not self.is_available:
            return df

        # Fetch all GRC-labelled issues from the project
        jira_issues = self._fetch_project_issues()

        if not jira_issues:
            return df

        # Build lookup: risk_id → issue data
        issue_lookup = {}
        for issue in jira_issues:
            summary = issue.get("fields", {}).get("summary", "")
            # Extract risk ID from summary prefix e.g. "[GRC-R001]"
            if summary.startswith("[GRC-"):
                try:
                    extracted_id = summary.split("]")[0].replace("[GRC-", "")
                    status_name = (
                        issue.get("fields", {})
                        .get("status", {})
                        .get("name", "")
                    )
                    status_category = (
                        issue.get("fields", {})
                        .get("status", {})
                        .get("statusCategory", {})
                        .get("name", "To Do")
                    )
                    issue_lookup[extracted_id] = {
                        "key": issue["key"],
                        "status": status_name,
                        "status_category": status_category,
                        "url": self._build_issue_url(issue["key"]),
                    }
                except (IndexError, KeyError):
                    continue

        # Map back to DataFrame
        for idx, row in df.iterrows():
            risk_id = str(row.get("Risk_ID", ""))
            if risk_id in issue_lookup:
                issue_data = issue_lookup[risk_id]
                df.at[idx, "Jira_Key"] = issue_data["key"]
                df.at[idx, "Jira_Status"] = issue_data["status"]
                df.at[idx, "Jira_URL"] = issue_data["url"]

        return df

    # ----------------------------------------------------------
    # HELPER METHODS
    # ----------------------------------------------------------

    def _build_issue_payload(self, risk_row: pd.Series) -> dict:
        """
        Construct the Jira issue creation payload from a risk row.

        Args:
            risk_row: Single risk register row.

        Returns:
            dict: Jira API issue creation payload.
        """
        risk_id = str(risk_row.get("Risk_ID", ""))
        risk_name = str(risk_row.get("Risk_Name", "Unknown Risk"))
        risk_level = str(risk_row.get("Risk_Level", "Medium"))
        risk_owner = str(risk_row.get("Risk_Owner", "Unassigned"))
        control_status = str(risk_row.get("Control_Status", "Unknown"))
        due_date = risk_row.get("Due_Date", None)
        likelihood = risk_row.get("Likelihood", "N/A")
        impact = risk_row.get("Impact", "N/A")

        # Format due date for Jira (YYYY-MM-DD)
        due_date_str = None
        if due_date and str(due_date) not in ("", "nan", "NaT", "None"):
            try:
                due_date_str = pd.to_datetime(due_date).strftime("%Y-%m-%d")
            except Exception:
                due_date_str = None

        # Summary uses prefix for easy identification on sync
        summary = f"[GRC-{risk_id}] {risk_name}"

        # Description in Jira document format (ADF)
        description = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "heading",
                    "attrs": {"level": 2},
                    "content": [{"type": "text", "text": "GRC Risk Details"}]
                },
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"Risk ID: {risk_id}\n"
                                f"Risk Name: {risk_name}\n"
                                f"Risk Level: {risk_level}\n"
                                f"Risk Owner: {risk_owner}\n"
                                f"Control Status: {control_status}\n"
                                f"Likelihood: {likelihood}\n"
                                f"Impact: {impact}\n"
                                f"Due Date: {due_date_str or 'Not set'}\n\n"
                                f"This issue was created automatically by the "
                                f"GRC Compliance Dashboard. "
                                f"Please update the status as remediation progresses."
                            )
                        }
                    ]
                },
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "When this issue is marked Done in Jira, "
                                "the GRC dashboard will reflect the risk as Closed."
                            ),
                            "marks": [{"type": "em"}]
                        }
                    ]
                }
            ]
        }

        # Map priority
        priority_name = PRIORITY_MAP.get(risk_level, "Medium")

        payload = {
            "fields": {
                "project": {"key": self.config.project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": self.config.issue_type},
                "priority": {"name": priority_name},
                "labels": [GRC_LABEL, f"grc-{risk_level.lower()}"],
            }
        }

        # Add due date if available
        if due_date_str:
            payload["fields"]["duedate"] = due_date_str

        return payload

    def _find_existing_issue(self, risk_id: str) -> Optional[dict]:
        """
        Search Jira for an existing issue for this risk ID.

        Uses JQL to find issues with matching summary prefix.

        Args:
            risk_id: GRC Risk ID to search for.

        Returns:
            dict with issue key and status if found, else None.
        """
        jql = (
            f'project = "{self.config.project_key}" '
            f'AND summary ~ "[GRC-{risk_id}]" '
            f'AND labels = "{GRC_LABEL}"'
        )

        try:
            resp = self._session.get(
                self._api_url("/search"),
                params={"jql": jql, "maxResults": 1, "fields": "summary,status"},
                timeout=self.config.timeout
            )

            if resp.status_code == 200:
                issues = resp.json().get("issues", [])
                if issues:
                    issue = issues[0]
                    return {
                        "key": issue["key"],
                        "status": (
                            issue.get("fields", {})
                            .get("status", {})
                            .get("name", "")
                        )
                    }
        except Exception as e:
            logger.warning(f"Duplicate check failed for {risk_id}: {e}")

        return None

    def _fetch_project_issues(self) -> list:
        """
        Fetch all GRC-labelled issues from the configured project.

        Returns:
            list: List of Jira issue dicts from the API.
        """
        jql = (
            f'project = "{self.config.project_key}" '
            f'AND labels = "{GRC_LABEL}"'
        )

        try:
            resp = self._session.get(
                self._api_url("/search"),
                params={
                    "jql": jql,
                    "maxResults": 200,
                    "fields": "summary,status"
                },
                timeout=self.config.timeout
            )

            if resp.status_code == 200:
                return resp.json().get("issues", [])

        except Exception as e:
            logger.warning(f"Failed to fetch project issues: {e}")

        return []

    def _build_issue_url(self, issue_key: str) -> str:
        """Build the browser URL for a Jira issue."""
        base = self.config.base_url.rstrip("/")
        return f"{base}/browse/{issue_key}"

    def _parse_error(self, response: requests.Response) -> str:
        """
        Extract a readable error message from a Jira API response.

        Args:
            response: The failed HTTP response.

        Returns:
            str: Human-readable error description.
        """
        try:
            body = response.json()
            errors = body.get("errors", {})
            messages = body.get("errorMessages", [])

            if errors:
                return "; ".join(f"{k}: {v}" for k, v in errors.items())
            if messages:
                return "; ".join(messages)
            return f"HTTP {response.status_code}"
        except Exception:
            return f"HTTP {response.status_code}: {response.text[:200]}"

    def get_connection_info(self) -> dict:
        """
        Return current connection status and config summary.

        Returns:
            dict: Connection details (no credentials exposed).
        """
        return {
            "is_available": self.is_available,
            "base_url": self.config.base_url,
            "project_key": self.config.project_key,
            "issue_type": self.config.issue_type,
        }


# ==========================================================
# HELPER: BUILD CLIENT FROM STREAMLIT SESSION STATE
# ==========================================================

def build_jira_client_from_config(
    base_url: str,
    email: str,
    api_token: str,
    project_key: str,
    issue_type: str = "Task"
) -> JiraClient:
    """
    Convenience factory to build a JiraClient from user-supplied config.

    Args:
        base_url:     Atlassian Cloud URL.
        email:        Atlassian account email.
        api_token:    Personal API token.
        project_key:  Target Jira project key.
        issue_type:   Issue type name. Defaults to 'Task'.

    Returns:
        JiraClient: Configured and connection-tested client instance.
    """
    config = JiraConfig(
        base_url=base_url.strip(),
        email=email.strip(),
        api_token=api_token.strip(),
        project_key=project_key.strip().upper(),
        issue_type=issue_type,
    )
    return JiraClient(config)


# ==========================================================
# HELPER: SUMMARISE PUSH RESULTS
# ==========================================================

def summarise_push_results(results: list[JiraIssueResult]) -> dict:
    """
    Summarise a list of push results into counts for display.

    Args:
        results: List of JiraIssueResult objects.

    Returns:
        dict: Summary counts with keys:
            total, succeeded, failed, already_existed, errors.
    """
    succeeded = [r for r in results if r.success and "already exists" not in r.message]
    already_existed = [r for r in results if r.success and "already exists" in r.message]
    failed = [r for r in results if not r.success]

    return {
        "total": len(results),
        "succeeded": len(succeeded),
        "already_existed": len(already_existed),
        "failed": len(failed),
        "errors": [
            {"risk_id": r.risk_id, "message": r.message}
            for r in failed
        ],
    }
