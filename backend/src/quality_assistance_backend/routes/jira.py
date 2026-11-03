import logging
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from quality_assistance_backend.config import settings
from quality_assistance_backend.db import get_db
from quality_assistance_backend.deps import get_current_user
from quality_assistance_backend.models import User
from quality_assistance_backend.schemas.jira import (
    JiraCreateIssueRequest,
    JiraCreatedIssue,
    JiraConnectionStatus,
    JiraIssue,
    JiraIssuePage,
    JiraOAuthStart,
    JiraProjectList,
)
from quality_assistance_backend.services import jira_cloud_service
from quality_assistance_backend.services.jira_cloud_service import JiraCloudError

router = APIRouter(prefix="/api/settings/jira", tags=["jira"])
logger = logging.getLogger(__name__)


def _settings_url(result: str, reason: str | None = None) -> str:
    target = settings.jira_frontend_url
    if not target:
        origins = settings.cors_origin_list
        target = f"{origins[0].rstrip('/')}/settings" if origins else "http://localhost:5173/settings"
    separator = "&" if "?" in target else "?"
    params = {"jira": result}
    if reason:
        params["jira_error"] = reason
    return f"{target}{separator}{urlencode(params)}"


@router.get("/status", response_model=JiraConnectionStatus)
async def jira_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JiraConnectionStatus:
    connection = await jira_cloud_service.get_connection(db, current_user.id)
    return jira_cloud_service.connection_status(connection)


@router.post("/connect", response_model=JiraOAuthStart)
async def start_jira_oauth(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JiraOAuthStart:
    try:
        state = await jira_cloud_service.create_oauth_state(db, current_user.id)
        return JiraOAuthStart(authorization_url=jira_cloud_service.authorization_url(state))
    except JiraCloudError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/callback")
async def jira_oauth_callback(
    state: str = Query(min_length=16, max_length=256),
    code: str | None = Query(default=None, max_length=4096),
    error: str | None = Query(default=None, max_length=128),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    if error or not code:
        try:
            await jira_cloud_service.consume_oauth_state(db, state)
        except JiraCloudError as exc:
            logger.warning(
                "jira.oauth_callback_failed status_code=%s reason=%s",
                exc.status_code,
                exc.reason,
            )
            result = "site-selection" if exc.status_code == 409 else "error"
            return RedirectResponse(
                _settings_url(result, None if result == "site-selection" else exc.reason),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        if error == "access_denied":
            logger.info("jira.oauth_callback_cancelled")
            return RedirectResponse(_settings_url("cancelled"), status_code=status.HTTP_303_SEE_OTHER)
        reason = "provider_error" if error else "missing_authorization_code"
        logger.warning("jira.oauth_callback_failed reason=%s", reason)
        return RedirectResponse(
            _settings_url("error", reason),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    try:
        user_id = await jira_cloud_service.consume_oauth_state(db, state)
        await jira_cloud_service.complete_oauth(db, user_id=user_id, code=code)
    except JiraCloudError as exc:
        logger.warning(
            "jira.oauth_callback_failed status_code=%s reason=%s",
            exc.status_code,
            exc.reason,
        )
        return RedirectResponse(
            _settings_url("error", exc.reason),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    return RedirectResponse(_settings_url("connected"), status_code=status.HTTP_303_SEE_OTHER)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_jira(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await jira_cloud_service.delete_connection(db, current_user.id)


@router.get("/issues", response_model=JiraIssuePage)
async def get_assigned_jira_issues(
    next_page_token: str | None = Query(default=None, max_length=4096),
    project_key: str | None = Query(
        default=None,
        max_length=64,
        pattern=r"^[A-Za-z][A-Za-z0-9_]*$",
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JiraIssuePage:
    try:
        return await jira_cloud_service.list_assigned_issues(
            db,
            user_id=current_user.id,
            next_page_token=next_page_token,
            project_key=project_key,
        )
    except JiraCloudError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/projects", response_model=JiraProjectList)
async def get_jira_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JiraProjectList:
    try:
        return await jira_cloud_service.list_projects(db, user_id=current_user.id)
    except JiraCloudError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/issues", response_model=JiraCreatedIssue, status_code=status.HTTP_201_CREATED)
async def create_jira_issue(
    issue: JiraCreateIssueRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JiraCreatedIssue:
    try:
        return await jira_cloud_service.create_issue(db, user_id=current_user.id, issue=issue)
    except JiraCloudError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/issues/{issue_key}", response_model=JiraIssue)
async def get_jira_issue_details(
    issue_key: str = Path(pattern=r"^[A-Za-z][A-Za-z0-9_]*-[0-9]+$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JiraIssue:
    try:
        return await jira_cloud_service.get_issue_details(
            db,
            user_id=current_user.id,
            issue_key=issue_key,
        )
    except JiraCloudError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
