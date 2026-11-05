from __future__ import annotations

import hashlib
import re
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
    JiraCreateIssueRequest,
    JiraCreatedIssue,
    JiraConnectionStatus,
    JiraIssue,
    JiraIssuePage,
    JiraProject,
    JiraProjectList,
)
from quality_assistance_backend.services.tls import create_ssl_context

ATLASSIAN_AUTHORIZE_URL = "https://auth.atlassian.com/authorize"
ATLASSIAN_TOKEN_URL = "https://auth.atlassian.com/oauth/token"
ATLASSIAN_RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"
ATLASSIAN_API_ROOT = "https://api.atlassian.com/ex/jira"
OAUTH_SCOPES = "read:jira-user read:jira-work write:jira-work offline_access"
OAUTH_PROVIDER_ERROR_REASONS = {
    "access_denied": "provider_access_denied",
    "invalid_request": "provider_invalid_request",
    "invalid_scope": "provider_invalid_scope",
    "server_error": "provider_server_error",
    "temporarily_unavailable": "provider_unavailable",
    "unauthorized_client": "unauthorized_client",
    "unsupported_grant_type": "unsupported_grant_type",
}

_encryptor = FernetEncryption()
_ssl_context = create_ssl_context()


class JiraCloudError(Exception):
    def __init__(
        self,
        status_code: int,
        message: str,
        reason: str = "callback_failed",
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.reason = reason


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


def _inline_markdown_to_adf(text: str) -> list[dict[str, object]]:
    pattern = re.compile(
        r"(?P<link>\[([^\]]+)\]\((https?://[^)\s]+)\))"
        r"|(?P<code>`([^`]+)`)"
        r"|(?P<strong>\*\*(.+?)\*\*|__(.+?)__)"
        r"|(?P<em>\*(\S(?:.*?\S)?)\*|_(\S(?:.*?\S)?)_)"
    )
    content: list[dict[str, object]] = []
    last_end = 0
    for match in pattern.finditer(text):
        if match.start() > last_end:
            content.append({"type": "text", "text": text[last_end:match.start()]})
        if match.group("link"):
            content.append(
                {
                    "type": "text",
                    "text": match.group(2),
                    "marks": [{"type": "link", "attrs": {"href": match.group(3)}}],
                }
            )
        elif match.group("code"):
            content.append(
                {
                    "type": "text",
                    "text": match.group(5),
                    "marks": [{"type": "code"}],
                }
            )
        elif match.group("strong"):
            content.append(
                {
                    "type": "text",
                    "text": match.group(7) or match.group(8),
                    "marks": [{"type": "strong"}],
                }
            )
        else:
            content.append(
                {
                    "type": "text",
                    "text": match.group(10) or match.group(11),
                    "marks": [{"type": "em"}],
                }
            )
        last_end = match.end()
    if last_end < len(text):
        content.append({"type": "text", "text": text[last_end:]})
    return content


def _markdown_to_adf(markdown: str) -> dict[str, object]:
    lines = markdown.splitlines()
    blocks: list[dict[str, object]] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue

        heading = re.match(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if heading:
            blocks.append(
                {
                    "type": "heading",
                    "attrs": {"level": len(heading.group(1))},
                    "content": _inline_markdown_to_adf(heading.group(2)),
                }
            )
            index += 1
            continue

        list_item = re.match(r"^(\s*)([-*+])\s+(.+)$", line)
        ordered_item = re.match(r"^(\s*)(\d+)[.)]\s+(.+)$", line)
        if list_item or ordered_item:
            is_ordered = ordered_item is not None
            first_item = ordered_item or list_item
            assert first_item is not None
            indentation = len(first_item.group(1).expandtabs(4))
            items: list[dict[str, object]] = []
            while index < len(lines):
                current = lines[index]
                current_match = (
                    re.match(r"^(\s*)(\d+)[.)]\s+(.+)$", current)
                    if is_ordered
                    else re.match(r"^(\s*)[-*+]\s+(.+)$", current)
                )
                if current_match is None:
                    break
                current_indent = len(current_match.group(1).expandtabs(4))
                if current_indent != indentation:
                    break
                item_text = current_match.group(3) if is_ordered else current_match.group(2)
                items.append(
                    {
                        "type": "listItem",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": _inline_markdown_to_adf(item_text),
                            }
                        ],
                    }
                )
                index += 1
            blocks.append(
                {
                    "type": "orderedList" if is_ordered else "bulletList",
                    "content": items,
                }
            )
            continue

        paragraph_lines = [line.strip()]
        index += 1
        while index < len(lines) and lines[index].strip():
            if re.match(r"^\s{0,3}#{1,6}\s+", lines[index]):
                break
            if re.match(r"^\s*[-*+]\s+|\s*\d+[.)]\s+", lines[index]):
                break
            paragraph_lines.append(lines[index].strip())
            index += 1
        blocks.append(
            {
                "type": "paragraph",
                "content": _inline_markdown_to_adf(" ".join(paragraph_lines)),
            }
        )
    return {"type": "doc", "version": 1, "content": blocks}


def _jira_validation_message(response: httpx.Response) -> str | None:
    try:
        body = response.json()
    except ValueError:
        return None
    if not isinstance(body, dict):
        return None

    messages = body.get("errorMessages")
    details = [
        message.strip()
        for message in messages
        if isinstance(message, str) and message.strip()
    ] if isinstance(messages, list) else []
    field_errors = body.get("errors")
    if isinstance(field_errors, dict):
        details.extend(
            f"{field}: {message.strip()}"
            for field, message in field_errors.items()
            if isinstance(field, str) and isinstance(message, str) and message.strip()
        )
    if not details:
        return None
    return "; ".join(details)[:1200]


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
        raise JiraCloudError(
            400,
            "Jira connection request expired or was invalid. Try connecting again.",
            reason="invalid_state",
        )
    user_id = record.user_id
    await db.delete(record)
    await db.commit()
    return user_id


async def _post_token(payload: dict[str, str]) -> dict[str, object]:
    try:
        async with httpx.AsyncClient(timeout=15.0, verify=_ssl_context) as client:
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
                raise JiraCloudError(
                    401,
                    "Atlassian rejected the authorization code. Check that the callback URL "
                    "matches exactly, then start a fresh Jira connection.",
                    reason="invalid_grant",
                )
            if (
                response.status_code in {400, 401, 403}
                and isinstance(error_response, dict)
                and error_response.get("error") == "invalid_client"
            ):
                raise JiraCloudError(
                    502,
                    "Atlassian rejected the OAuth client credentials. Confirm the Client ID "
                    "and Secret belong to the same OAuth app, then restart the backend.",
                    reason="invalid_client",
                )
            error_code = error_response.get("error") if isinstance(error_response, dict) else None
            reason = OAUTH_PROVIDER_ERROR_REASONS.get(error_code, "token_exchange_failed")
            raise JiraCloudError(
                502,
                "Atlassian could not complete the OAuth exchange. Confirm the OAuth app "
                "configuration and callback URL, then start a fresh connection.",
                reason=reason,
            )
        try:
            token_data = response.json()
        except ValueError as exc:
            raise JiraCloudError(
                502,
                "Atlassian returned an invalid OAuth response.",
                reason="invalid_provider_response",
            ) from exc
    except httpx.HTTPError as exc:
        raise JiraCloudError(
            502,
            "Could not reach Atlassian to complete OAuth.",
            reason="provider_unreachable",
        ) from exc
    if not isinstance(token_data, dict) or not token_data.get("access_token"):
        raise JiraCloudError(
            502,
            "Atlassian returned an invalid OAuth response.",
            reason="invalid_provider_response",
        )
    return token_data


def _token_expiry(token_data: dict[str, object]) -> datetime:
    expires_in = token_data.get("expires_in")
    if not isinstance(expires_in, (int, float)) or expires_in <= 0:
        raise JiraCloudError(
            502,
            "Atlassian returned an invalid token expiry.",
            reason="invalid_provider_response",
        )
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
        raise JiraCloudError(
            502,
            "Atlassian did not issue a refresh token. Enable the offline_access scope and reconnect.",
            reason="missing_offline_access",
        )

    try:
        async with httpx.AsyncClient(timeout=15.0, verify=_ssl_context) as client:
            response = await client.get(
                ATLASSIAN_RESOURCES_URL,
                headers={"Authorization": f"Bearer {token_data['access_token']}"},
            )
        if response.is_error:
            raise JiraCloudError(
                502,
                "Could not retrieve the Jira sites available to this Atlassian account.",
                reason="site_lookup_failed",
            )
        try:
            resources = response.json()
        except ValueError as exc:
            raise JiraCloudError(
                502,
                "Atlassian returned invalid Jira site information.",
                reason="invalid_site_response",
            ) from exc
    except httpx.HTTPError as exc:
        raise JiraCloudError(
            502,
            "Could not reach Atlassian to list available Jira sites.",
            reason="provider_unreachable",
        ) from exc

    if not isinstance(resources, list) or not resources:
        raise JiraCloudError(
            403,
            "This Atlassian account has no Jira sites available to the app.",
            reason="no_jira_site",
        )
    jira_resources_by_id = {
        resource["id"]: resource
        for resource in resources
        if isinstance(resource, dict)
        and isinstance(resource.get("id"), str)
        and isinstance(resource.get("scopes"), list)
        and {"read:jira-user", "read:jira-work", "write:jira-work"}.issubset(
            set(resource["scopes"])
        )
    }
    jira_resources = list(jira_resources_by_id.values())
    if not jira_resources:
        raise JiraCloudError(
            403,
            "No accessible Jira site has the required Jira scopes. Grant read:jira-user, "
            "read:jira-work, and write:jira-work, then reconnect.",
            reason="missing_jira_scopes",
        )
    if len(jira_resources) > 1:
        raise JiraCloudError(
            409,
            "More than one Jira site is authorized. Reconnect and authorize only the office Jira site.",
            reason="multiple_jira_sites",
        )
    resource = jira_resources[0]
    if not isinstance(resource, dict) or not all(
        isinstance(resource.get(field), str) and resource[field]
        for field in ("id", "name", "url")
    ):
        raise JiraCloudError(
            502,
            "Atlassian returned invalid Jira site information.",
            reason="invalid_site_response",
        )
    parsed_site_url = urlparse(resource["url"])
    if parsed_site_url.scheme != "https" or not parsed_site_url.netloc:
        raise JiraCloudError(
            502,
            "Atlassian returned an invalid Jira site URL.",
            reason="invalid_site_response",
        )

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


async def _jira_account_id(client: httpx.AsyncClient, cloud_id: str, access_token: str) -> str:
    response = await client.get(
        f"{ATLASSIAN_API_ROOT}/{cloud_id}/rest/api/3/myself",
        params={},
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        },
    )
    if response.status_code == 401:
        raise JiraCloudError(401, "Jira authorization expired. Reconnect Jira in Settings.")
    if response.status_code == 403:
        raise JiraCloudError(
            403,
            "Jira denied access. Ask your Jira administrator to approve the app scopes.",
        )
    if response.is_error:
        raise JiraCloudError(502, "Could not identify your Jira account.")
    try:
        myself = response.json()
    except ValueError as exc:
        raise JiraCloudError(502, "Jira returned invalid account information.") from exc
    if (
        not isinstance(myself, dict)
        or not isinstance(myself.get("accountId"), str)
        or not myself["accountId"]
    ):
        raise JiraCloudError(502, "Jira returned invalid account information.")
    return myself["accountId"]


async def list_assigned_issues(
    db: AsyncSession,
    *,
    user_id: UUID,
    next_page_token: str | None = None,
    project_key: str | None = None,
) -> JiraIssuePage:
    if project_key is not None and not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", project_key):
        raise JiraCloudError(422, "Select a valid Jira project.")
    connection = await get_connection(db, user_id)
    if connection is None:
        raise JiraCloudError(409, "Connect your Jira account in Settings to view issues.")
    access_token = await _access_token(db, connection)
    params: dict[str, str | int] = {
        "maxResults": 50,
        "fields": "summary,issuetype,status",
    }
    if next_page_token:
        params["nextPageToken"] = next_page_token
    url = f"{ATLASSIAN_API_ROOT}/{connection.cloud_id}/rest/api/3/search/jql"
    try:
        async with httpx.AsyncClient(timeout=20.0, verify=_ssl_context) as client:
            if project_key:
                params["jql"] = f'project = "{project_key}" ORDER BY updated DESC'
            else:
                account_id = await _jira_account_id(client, connection.cloud_id, access_token)
                account_id = account_id.replace("\\", "\\\\").replace('"', '\\"')
                params["jql"] = f'assignee = "{account_id}" ORDER BY updated DESC'
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
            raise JiraCloudError(502, "Could not retrieve Jira issues.")
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
        raise JiraCloudError(409, "Connect your Jira account in Settings to view issues.")
    access_token = await _access_token(db, connection)
    url = f"{ATLASSIAN_API_ROOT}/{connection.cloud_id}/rest/api/3/search/jql"
    try:
        async with httpx.AsyncClient(timeout=20.0, verify=_ssl_context) as client:
            response = await client.get(
                url,
                params={
                    "jql": f'key = "{issue_key}"',
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
        raise JiraCloudError(404, "The issue is not accessible to your connected Jira account.")
    return _issue_from_payload(result["issues"][0])


async def list_projects(
    db: AsyncSession,
    *,
    user_id: UUID,
) -> JiraProjectList:
    connection = await get_connection(db, user_id)
    if connection is None:
        raise JiraCloudError(409, "Connect your Jira account in Settings to create issues.")
    access_token = await _access_token(db, connection)
    url = f"{ATLASSIAN_API_ROOT}/{connection.cloud_id}/rest/api/3/project/search"
    try:
        async with httpx.AsyncClient(timeout=20.0, verify=_ssl_context) as client:
            response = await client.get(
                url,
                params={"maxResults": 100, "orderBy": "name"},
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            )
        if response.status_code == 401:
            raise JiraCloudError(401, "Jira authorization expired. Reconnect Jira in Settings.")
        if response.status_code == 403:
            raise JiraCloudError(403, "Jira denied access to the project list.")
        if response.is_error:
            raise JiraCloudError(502, "Could not retrieve Jira projects.")
        try:
            result = response.json()
        except ValueError as exc:
            raise JiraCloudError(502, "Jira returned an invalid project list.") from exc
    except httpx.HTTPError as exc:
        raise JiraCloudError(502, "Could not reach Jira to retrieve projects.") from exc

    values = result.get("values") if isinstance(result, dict) else None
    if not isinstance(values, list):
        raise JiraCloudError(502, "Jira returned an invalid project list.")
    projects = [
        JiraProject(id=project["id"], key=project["key"], name=project["name"])
        for project in values
        if isinstance(project, dict)
        and all(isinstance(project.get(field), str) and project[field] for field in ("id", "key", "name"))
    ]
    return JiraProjectList(projects=projects)


async def create_issue(
    db: AsyncSession,
    *,
    user_id: UUID,
    issue: JiraCreateIssueRequest,
) -> JiraCreatedIssue:
    connection = await get_connection(db, user_id)
    if connection is None:
        raise JiraCloudError(409, "Connect your Jira account in Settings to create issues.")
    access_token = await _access_token(db, connection)
    payload = {
        "fields": {
            "project": {"key": issue.project_key},
            "summary": issue.summary,
            "issuetype": {"name": "Bug"},
            "description": _markdown_to_adf(issue.description),
        }
    }
    url = f"{ATLASSIAN_API_ROOT}/{connection.cloud_id}/rest/api/3/issue"
    try:
        async with httpx.AsyncClient(timeout=20.0, verify=_ssl_context) as client:
            response = await client.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            )
        if response.status_code == 401:
            raise JiraCloudError(
                401,
                "Jira rejected authorization for issue creation. Reconnect Jira in Settings and "
                "approve the write:jira-work scope, then try again. Confirm you have Create Issues "
                "permission in the selected project.",
            )
        if response.status_code == 403:
            raise JiraCloudError(
                403,
                "Jira denied issue creation. Grant write:jira-work to the OAuth app, reconnect Jira "
                "in Settings, and confirm you have Create Issues permission in the selected project.",
            )
        if response.status_code == 400:
            validation_message = _jira_validation_message(response)
            if validation_message:
                raise JiraCloudError(
                    400,
                    f"Jira rejected the Bug issue fields: {validation_message}",
                )
            raise JiraCloudError(
                400,
                "Jira could not create this Bug in the selected project. Confirm the project allows "
                "Bug issues and that its required fields are satisfied.",
            )
        if response.is_error:
            raise JiraCloudError(502, "Could not create the Jira issue.")
        try:
            result = response.json()
        except ValueError as exc:
            raise JiraCloudError(502, "Jira returned an invalid created-issue response.") from exc
    except httpx.HTTPError as exc:
        raise JiraCloudError(502, "Could not reach Jira to create the issue.") from exc

    if not isinstance(result, dict) or not all(
        isinstance(result.get(field), str) and result[field]
        for field in ("id", "key")
    ):
        raise JiraCloudError(502, "Jira returned an invalid created-issue response.")
    return JiraCreatedIssue(
        id=result["id"],
        key=result["key"],
        summary=issue.summary,
        url=f"{connection.site_url.rstrip('/')}/browse/{result['key']}",
    )
