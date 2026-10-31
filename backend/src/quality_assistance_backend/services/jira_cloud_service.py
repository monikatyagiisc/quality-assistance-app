from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode, urlparse
from uuid import UUID

import httpx
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from quality_assistance_backend.config import settings
from quality_assistance_backend.crypto.fernet_encryption import FernetEncryption
from quality_assistance_backend.models import JiraConnection, JiraOAuthState
from quality_assistance_backend.schemas.jira import (
    JiraConnectionStatus,
    JiraIssue,
    JiraIssuePage,
)

ATLASSIAN_AUTHORIZE_URL = "https://auth.atlassian.com/authorize"
ATLASSIAN_TOKEN_URL = "https://auth.atlassian.com/oauth/token"
ATLASSIAN_RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"
ATLASSIAN_API_ROOT = "https://api.atlassian.com/ex/jira"
OAUTH_SCOPES = "read:jira-user read:jira-work offline_access"

_encryptor = FernetEncryption()


class JiraCloudError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _state_digest(state: str) -> str:
    return hashlib.sha256(state.encode("utf-8")).hexdigest()


def _extract_adf_text(value: object) -> str:
    if not isinstance(value, dict):
        return ""
    node_type = value.get("type")
    if node_type == "text":
        return str(value.get("text", ""))
    if node_type == "hardBreak":
        return "\n"

    content = value.get("content")
    if not isinstance(content, list):
        return ""

    separator = "\n" if node_type in {"paragraph", "heading", "listItem", "codeBlock"} else ""
    children = "".join(_extract_adf_text(child) for child in content)
    if separator:
        return f"{children}{separator}"
    return children


def _plain_description(value: object) -> str:
    text = _extract_adf_text(value)
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def connection_status(connection: JiraConnection | None) -> JiraConnectionStatus:
    return JiraConnectionStatus(
        configured=settings.jira_oauth_enabled,
        connected=connection is not None,
        site_name=connection.site_name if connection else None,
        site_url=connection.site_url if connection else None,
    )


async def get_connection(db: AsyncSession, user_id: UUID) -> JiraConnection | None:
    result = await db.execute(
        select(JiraConnection).where(JiraConnection.user_id == user_id)
    )
    return result.scalar_one_or_none()


def authorization_url(state: str) -> str:
    if not settings.jira_oauth_enabled:
        raise JiraCloudError(503, "Jira OAuth is not configured by the application administrator.")
    params = {
        "audience": "api.atlassian.com",
        "client_id": settings.jira_client_id,
        "scope": OAUTH_SCOPES,
        "redirect_uri": settings.jira_redirect_uri,
        "state": state,
        "response_type": "code",
        "prompt": "consent",
    }
    return f"{ATLASSIAN_AUTHORIZE_URL}?{urlencode(params)}"


async def create_oauth_state(db: AsyncSession, user_id: UUID) -> str:
    if not settings.jira_oauth_enabled:
        raise JiraCloudError(503, "Jira OAuth is not configured by the application administrator.")
    state = secrets.token_urlsafe(32)
    await db.execute(delete(JiraOAuthState).where(JiraOAuthState.expires_at <= _now()))
    db.add(
        JiraOAuthState(
            state_digest=_state_digest(state),
            user_id=user_id,
            expires_at=_now() + timedelta(minutes=10),
        )
    )
    await db.commit()
    return state


async def consume_oauth_state(db: AsyncSession, state: str) -> UUID:
    record = await db.scalar(
        select(JiraOAuthState)
        .where(
            JiraOAuthState.state_digest == _state_digest(state),
            JiraOAuthState.expires_at > _now(),
        )
        .with_for_update()
    )
    if record is None:
        raise JiraCloudError(400, "Jira connection request expired or was invalid. Try connecting again.")
    user_id = record.user_id
    await db.delete(record)
    await db.commit()
    return user_id


async def _post_token(payload: dict[str, str]) -> dict[str, object]:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(ATLASSIAN_TOKEN_URL, json=payload)
        if response.is_error:
            try:
                error_response = response.json() if response.content else {}
            except ValueError:
                error_response = {}
            if (
                response.status_code in {400, 403}
                and isinstance(error_response, dict)
                and error_response.get("error") == "invalid_grant"
            ):
                raise JiraCloudError(401, "Jira authorization expired. Reconnect Jira in Settings.")
            raise JiraCloudError(502, "Atlassian could not complete the OAuth exchange.")
        try:
            token_data = response.json()
        except ValueError as exc:
            raise JiraCloudError(502, "Atlassian returned an invalid OAuth response.") from exc
    except httpx.HTTPError as exc:
        raise JiraCloudError(502, "Could not reach Atlassian to complete OAuth.") from exc
    if not isinstance(token_data, dict) or not token_data.get("access_token"):
        raise JiraCloudError(502, "Atlassian returned an invalid OAuth response.")
    return token_data


def _token_expiry(token_data: dict[str, object]) -> datetime:
    expires_in = token_data.get("expires_in")
    if not isinstance(expires_in, (int, float)) or expires_in <= 0:
        raise JiraCloudError(502, "Atlassian returned an invalid token expiry.")
    return _now() + timedelta(seconds=int(expires_in))


async def complete_oauth(
    db: AsyncSession,
    *,
    user_id: UUID,
    code: str,
) -> None:
    token_data = await _post_token(
        {
            "grant_type": "authorization_code",
            "client_id": settings.jira_client_id or "",
            "client_secret": (
                settings.jira_client_secret.get_secret_value()
                if settings.jira_client_secret
                else ""
            ),
            "code": code,
            "redirect_uri": settings.jira_redirect_uri or "",
        }
    )
    refresh_token = token_data.get("refresh_token")
    if not isinstance(refresh_token, str) or not refresh_token:
        raise JiraCloudError(502, "Atlassian did not issue a refresh token. Recheck offline_access configuration.")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                ATLASSIAN_RESOURCES_URL,
                headers={"Authorization": f"Bearer {token_data['access_token']}"},
            )
        if response.is_error:
            raise JiraCloudError(502, "Could not retrieve the Jira sites available to this Atlassian account.")
        try:
            resources = response.json()
        except ValueError as exc:
            raise JiraCloudError(502, "Atlassian returned invalid Jira site information.") from exc
    except httpx.HTTPError as exc:
        raise JiraCloudError(502, "Could not reach Atlassian to list available Jira sites.") from exc

    if not isinstance(resources, list) or not resources:
        raise JiraCloudError(403, "This Atlassian account has no Jira sites available to the app.")
    jira_resources_by_id = {
        resource["id"]: resource
        for resource in resources
        if isinstance(resource, dict)
        and isinstance(resource.get("id"), str)
        and isinstance(resource.get("scopes"), list)
        and {"read:jira-user", "read:jira-work"}.issubset(set(resource["scopes"]))
    }
    jira_resources = list(jira_resources_by_id.values())
    if not jira_resources:
        raise JiraCloudError(403, "No accessible Jira site has the required Jira read scopes.")
    if len(jira_resources) > 1:
        raise JiraCloudError(
            409,
            "More than one Jira site is authorized. Reconnect and authorize only the office Jira site.",
        )
    resource = jira_resources[0]
    if not isinstance(resource, dict) or not all(
        isinstance(resource.get(field), str) and resource[field]
        for field in ("id", "name", "url")
    ):
        raise JiraCloudError(502, "Atlassian returned invalid Jira site information.")
    parsed_site_url = urlparse(resource["url"])
    if parsed_site_url.scheme != "https" or not parsed_site_url.netloc:
        raise JiraCloudError(502, "Atlassian returned an invalid Jira site URL.")

    connection = await get_connection(db, user_id)
    if connection is None:
        connection = JiraConnection(user_id=user_id)
        db.add(connection)
    connection.cloud_id = resource["id"]
    connection.site_name = resource["name"]
    connection.site_url = resource["url"]
    connection.access_token_encrypted = _encryptor.encrypt(str(token_data["access_token"]))
    connection.refresh_token_encrypted = _encryptor.encrypt(refresh_token)
    connection.expires_at = _token_expiry(token_data)
    await db.commit()


async def delete_connection(db: AsyncSession, user_id: UUID) -> None:
    connection = await get_connection(db, user_id)
    if connection is not None:
        await db.delete(connection)
        await db.commit()


async def _access_token(db: AsyncSession, connection: JiraConnection) -> str:
    if connection.expires_at > _now() + timedelta(seconds=60):
        return _encryptor.decrypt(connection.access_token_encrypted)

    refresh_token = _encryptor.decrypt(connection.refresh_token_encrypted)
    token_data = await _post_token(
        {
            "grant_type": "refresh_token",
            "client_id": settings.jira_client_id or "",
            "client_secret": (
                settings.jira_client_secret.get_secret_value()
                if settings.jira_client_secret
                else ""
            ),
            "refresh_token": refresh_token,
        }
    )

    new_refresh_token = token_data.get("refresh_token")
    if not isinstance(new_refresh_token, str) or not new_refresh_token:
        raise JiraCloudError(502, "Atlassian returned an invalid refresh token.")
    access_token = str(token_data["access_token"])
    connection.access_token_encrypted = _encryptor.encrypt(access_token)
    connection.refresh_token_encrypted = _encryptor.encrypt(new_refresh_token)
    connection.expires_at = _token_expiry(token_data)
    await db.commit()
    return access_token


def _issue_from_payload(payload: object) -> JiraIssue:
    if not isinstance(payload, dict) or not isinstance(payload.get("fields"), dict):
        raise JiraCloudError(502, "Atlassian returned an invalid Jira issue.")
    fields = payload["fields"]
    issue_type = fields.get("issuetype")
    status = fields.get("status")
    summary = fields.get("summary")
    return JiraIssue(
        id=str(payload.get("id", "")),
        key=str(payload.get("key", "")),
        summary=summary if isinstance(summary, str) else "",
        description=_plain_description(fields.get("description")),
        issue_type=issue_type.get("name") if isinstance(issue_type, dict) else None,
        status=status.get("name") if isinstance(status, dict) else None,
    )


async def list_assigned_issues(
    db: AsyncSession,
    *,
    user_id: UUID,
    next_page_token: str | None = None,
) -> JiraIssuePage:
    connection = await get_connection(db, user_id)
    if connection is None:
        raise JiraCloudError(409, "Connect your Jira account in Settings to view assigned issues.")
    access_token = await _access_token(db, connection)
    params: dict[str, str | int] = {
        "jql": "assignee = currentUser() ORDER BY updated DESC",
        "maxResults": 50,
        "fields": "summary,issuetype,status",
    }
    if next_page_token:
        params["nextPageToken"] = next_page_token
    url = f"{ATLASSIAN_API_ROOT}/{connection.cloud_id}/rest/api/3/search/jql"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                url,
                params=params,
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            )
        if response.status_code == 401:
            raise JiraCloudError(401, "Jira authorization expired. Reconnect Jira in Settings.")
        if response.status_code == 403:
            raise JiraCloudError(403, "Jira denied access. Ask your Jira administrator to approve the app scopes.")
        if response.is_error:
            raise JiraCloudError(502, "Could not retrieve assigned issues from Jira.")
        try:
            result = response.json()
        except ValueError as exc:
            raise JiraCloudError(502, "Jira returned an invalid issue list.") from exc
    except httpx.HTTPError as exc:
        raise JiraCloudError(502, "Could not reach Jira to retrieve assigned issues.") from exc

    if not isinstance(result, dict) or not isinstance(result.get("issues"), list):
        raise JiraCloudError(502, "Jira returned an invalid issue list.")
    issues = [_issue_from_payload(issue) for issue in result["issues"]]
    next_token = result.get("nextPageToken")
    return JiraIssuePage(
        issues=issues,
        next_page_token=next_token if isinstance(next_token, str) and next_token else None,
    )


async def get_issue_details(
    db: AsyncSession,
    *,
    user_id: UUID,
    issue_key: str,
) -> JiraIssue:
    connection = await get_connection(db, user_id)
    if connection is None:
        raise JiraCloudError(409, "Connect your Jira account in Settings to view assigned issues.")
    access_token = await _access_token(db, connection)
    url = f"{ATLASSIAN_API_ROOT}/{connection.cloud_id}/rest/api/3/search/jql"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                url,
                params={
                    "jql": f'key = "{issue_key}" AND assignee = currentUser()',
                    "maxResults": 1,
                    "fields": "summary,description,issuetype,status",
                },
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            )
        if response.status_code == 401:
            raise JiraCloudError(401, "Jira authorization expired. Reconnect Jira in Settings.")
        if response.status_code == 403:
            raise JiraCloudError(403, "Jira denied access to this issue.")
        if response.is_error:
            raise JiraCloudError(502, "Could not retrieve the selected issue from Jira.")
        try:
            result = response.json()
        except ValueError as exc:
            raise JiraCloudError(502, "Jira returned invalid issue details.") from exc
    except httpx.HTTPError as exc:
        raise JiraCloudError(502, "Could not reach Jira to retrieve the selected issue.") from exc
    if not isinstance(result, dict) or not isinstance(result.get("issues"), list):
        raise JiraCloudError(502, "Jira returned invalid issue details.")
    if not result["issues"]:
        raise JiraCloudError(404, "The issue is no longer assigned to you or is not accessible.")
    return _issue_from_payload(result["issues"][0])
