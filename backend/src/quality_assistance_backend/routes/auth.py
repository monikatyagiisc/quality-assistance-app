from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from quality_assistance_backend.config import settings
from quality_assistance_backend.db import get_db
from quality_assistance_backend.deps import get_current_user
from quality_assistance_backend.models import User
from quality_assistance_backend.schemas import LoginInput, RegisterInput, TokenResponse, UserPublic
from quality_assistance_backend.schemas.auth import EntraTicketInput
from quality_assistance_backend.services import entra_sso_service
from quality_assistance_backend.services.entra_sso_service import EntraSSOError
from quality_assistance_backend.security import (
    create_access_token,
    get_user_by_email,
    store_password,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _entra_frontend_url(result: str | None = None, ticket: str | None = None) -> str:
    target = settings.entra_frontend_url or "http://localhost:5173/login"
    parts = urlsplit(target)
    if result:
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        query["sso"] = result
        path = "/settings" if result == "linked" else parts.path
        parts = parts._replace(path=path, query=urlencode(query), fragment="")
    if ticket:
        parts = parts._replace(fragment=urlencode({"sso_ticket": ticket}))
    return urlunsplit(parts)


@router.get("/entra/status")
async def entra_sso_status() -> dict[str, bool]:
    return {"enabled": settings.entra_sso_enabled}


@router.post("/entra/start")
async def start_entra_sign_in(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    try:
        return {"authorization_url": await entra_sso_service.create_oauth_request(db)}
    except EntraSSOError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/entra/account")
async def entra_account_status(
    current_user: User = Depends(get_current_user),
) -> dict[str, bool]:
    return {
        "enabled": settings.entra_sso_enabled,
        "linked": bool(current_user.entra_tenant_id and current_user.entra_object_id),
    }


@router.post("/entra/link/start")
async def start_entra_account_link(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    try:
        return {
            "authorization_url": await entra_sso_service.create_oauth_request(
                db,
                user_id=current_user.id,
            )
        }
    except EntraSSOError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/entra/callback")
async def entra_sign_in_callback(
    state: str = Query(min_length=16, max_length=256),
    code: str | None = Query(default=None, max_length=4096),
    error: str | None = Query(default=None, max_length=128),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    if error or not code:
        return RedirectResponse(_entra_frontend_url(result="error"), status_code=303)
    try:
        result = await entra_sso_service.complete_sign_in(db, state=state, code=code)
    except EntraSSOError as exc:
        if exc.code == "link_required":
            return RedirectResponse(_entra_frontend_url(result="link-required"), status_code=303)
        return RedirectResponse(_entra_frontend_url(result="error"), status_code=303)
    if result.linked:
        return RedirectResponse(_entra_frontend_url(result="linked"), status_code=303)
    if result.ticket:
        return RedirectResponse(_entra_frontend_url(ticket=result.ticket), status_code=303)
    return RedirectResponse(_entra_frontend_url(result="error"), status_code=303)


@router.post("/entra/exchange", response_model=TokenResponse)
async def exchange_entra_login_ticket(
    payload: EntraTicketInput,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    try:
        return await entra_sso_service.exchange_login_ticket(db, payload.ticket)
    except EntraSSOError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterInput, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    existing = await get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name.strip(),
        password_hash=store_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginInput, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await get_user_by_email(db, payload.email)
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))


@router.get("/me", response_model=UserPublic)
async def me(current_user: User = Depends(get_current_user)) -> UserPublic:
    return UserPublic.model_validate(current_user)
