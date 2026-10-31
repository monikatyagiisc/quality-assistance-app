from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from uuid import UUID

import httpx
from jose import JWTError, jwk, jwt
from jose.exceptions import JWKError
from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from quality_assistance_backend.config import settings
from quality_assistance_backend.models import EntraLoginTicket, EntraOAuthState, User
from quality_assistance_backend.schemas.auth import TokenResponse, UserPublic
from quality_assistance_backend.security import (
    create_access_token,
    get_user_by_email,
    get_user_by_entra_identity,
)

ENTRA_AUTHORITY = "https://login.microsoftonline.com"
EMAIL_ADAPTER = TypeAdapter(EmailStr)


class EntraSSOError(Exception):
    def __init__(self, status_code: int, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code


@dataclass(frozen=True)
class EntraSignInResult:
    ticket: str | None = None
    linked: bool = False


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def authorization_url(state: str, nonce: str, code_verifier: str) -> str:
    if not settings.entra_sso_enabled:
        raise EntraSSOError(503, "Microsoft Entra SSO is not configured by the application administrator.")
    challenge = _base64url(hashlib.sha256(code_verifier.encode("ascii")).digest())
    params = {
        "client_id": settings.entra_client_id,
        "response_type": "code",
        "redirect_uri": settings.entra_redirect_uri,
        "response_mode": "query",
        "scope": "openid profile email",
        "state": state,
        "nonce": nonce,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    return (
        f"{ENTRA_AUTHORITY}/{settings.entra_tenant_id}/oauth2/v2.0/authorize?"
        f"{urlencode(params)}"
    )


async def create_oauth_request(db: AsyncSession, user_id: UUID | None = None) -> str:
    if not settings.entra_sso_enabled:
        raise EntraSSOError(503, "Microsoft Entra SSO is not configured by the application administrator.")
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(64)
    await db.execute(delete(EntraOAuthState).where(EntraOAuthState.expires_at <= _now()))
    db.add(
        EntraOAuthState(
            state_digest=_digest(state),
            nonce_digest=_digest(nonce),
            code_verifier=code_verifier,
            user_id=user_id,
            flow="link" if user_id else "login",
            expires_at=_now() + timedelta(minutes=10),
        )
    )
    await db.commit()
    return authorization_url(state, nonce, code_verifier)


async def _consume_oauth_request(
    db: AsyncSession,
    state: str,
) -> EntraOAuthState:
    request = await db.scalar(
        select(EntraOAuthState)
        .where(
            EntraOAuthState.state_digest == _digest(state),
            EntraOAuthState.expires_at > _now(),
        )
        .with_for_update()
    )
    if request is None:
        raise EntraSSOError(400, "Microsoft sign-in expired or was invalid. Try again.")
    await db.delete(request)
    await db.commit()
    return request


async def _exchange_code(code: str, code_verifier: str) -> str:
    payload = {
        "client_id": settings.entra_client_id or "",
        "client_secret": (
            settings.entra_client_secret.get_secret_value()
            if settings.entra_client_secret
            else ""
        ),
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.entra_redirect_uri or "",
        "code_verifier": code_verifier,
        "scope": "openid profile email",
    }
    token_url = f"{ENTRA_AUTHORITY}/{settings.entra_tenant_id}/oauth2/v2.0/token"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(token_url, data=payload)
        if response.is_error:
            raise EntraSSOError(401, "Microsoft sign-in could not be completed. Try again.")
        token_data = response.json()
    except EntraSSOError:
        raise
    except (httpx.HTTPError, ValueError) as exc:
        raise EntraSSOError(502, "Could not reach Microsoft to complete sign-in.") from exc
    id_token = token_data.get("id_token") if isinstance(token_data, dict) else None
    if not isinstance(id_token, str) or not id_token:
        raise EntraSSOError(502, "Microsoft did not return a valid sign-in token.")
    return id_token


async def _validate_id_token(id_token: str, nonce_digest: str) -> dict[str, object]:
    try:
        header = jwt.get_unverified_header(id_token)
    except JWTError as exc:
        raise EntraSSOError(401, "Microsoft returned an invalid sign-in token.") from exc
    key_id = header.get("kid")
    if not isinstance(key_id, str):
        raise EntraSSOError(401, "Microsoft returned an invalid sign-in token.")

    keys_url = f"{ENTRA_AUTHORITY}/{settings.entra_tenant_id}/discovery/v2.0/keys"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(keys_url)
        response.raise_for_status()
        key_data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise EntraSSOError(502, "Could not retrieve Microsoft sign-in verification keys.") from exc
    keys = key_data.get("keys") if isinstance(key_data, dict) else None
    signing_key = next(
        (
            key
            for key in keys or []
            if isinstance(key, dict) and key.get("kid") == key_id and key.get("kty") == "RSA"
        ),
        None,
    )
    if signing_key is None:
        raise EntraSSOError(401, "Microsoft returned an unrecognized sign-in token.")

    tenant_id = settings.entra_tenant_id or ""
    issuer = f"{ENTRA_AUTHORITY}/{tenant_id}/v2.0"
    try:
        public_key = jwk.construct(signing_key, algorithm="RS256")
        claims = jwt.decode(
            id_token,
            public_key,
            algorithms=["RS256"],
            audience=settings.entra_client_id,
            issuer=issuer,
            options={"require_exp": True, "require_iat": True, "require_sub": True},
        )
    except (JWKError, JWTError) as exc:
        raise EntraSSOError(401, "Microsoft sign-in token validation failed.") from exc

    nonce = claims.get("nonce")
    try:
        claim_tenant_id = str(UUID(str(claims.get("tid", ""))))
    except ValueError:
        claim_tenant_id = ""
    if (
        not isinstance(nonce, str)
        or not hmac.compare_digest(_digest(nonce), nonce_digest)
        or claim_tenant_id != tenant_id
    ):
        raise EntraSSOError(401, "Microsoft sign-in token validation failed.")
    return claims


def _identity_fields(claims: dict[str, object]) -> tuple[str, str, str, str]:
    try:
        tenant_id = str(UUID(str(claims.get("tid", ""))))
        object_id = str(UUID(str(claims.get("oid", ""))))
        email = str(EMAIL_ADAPTER.validate_python(claims.get("email"))).lower()
    except (ValueError, ValidationError) as exc:
        raise EntraSSOError(
            403,
            "Your Microsoft account must include a valid email address. Ask your administrator to add the email ID token claim.",
        ) from exc
    name = claims.get("name")
    full_name = name.strip()[:255] if isinstance(name, str) and name.strip() else email.split("@", 1)[0]
    return tenant_id, object_id, email, full_name


async def _find_or_create_user(
    db: AsyncSession,
    claims: dict[str, object],
) -> User:
    tenant_id, object_id, email, full_name = _identity_fields(claims)
    user = await get_user_by_entra_identity(db, tenant_id, object_id)
    if user is not None:
        return user

    user = await get_user_by_email(db, email)
    if user is not None:
        raise EntraSSOError(
            409,
            "This email already has an app account. Sign in with that account and link Microsoft from Settings before using SSO.",
            code="link_required",
        )

    user = User(email=email, full_name=full_name, password_hash=None)
    db.add(user)
    user.entra_tenant_id = tenant_id
    user.entra_object_id = object_id
    await db.flush()
    return user


async def _link_identity(
    db: AsyncSession,
    *,
    user: User,
    tenant_id: str,
    object_id: str,
    email: str,
) -> None:
    if email != user.email.lower():
        raise EntraSSOError(403, "The Microsoft account email must match this app account before it can be linked.")
    identity_owner = await get_user_by_entra_identity(db, tenant_id, object_id)
    if identity_owner is not None and identity_owner.id != user.id:
        raise EntraSSOError(409, "This Microsoft identity is already linked to another app account.")
    if user.entra_object_id and (
        user.entra_object_id != object_id or user.entra_tenant_id != tenant_id
    ):
        raise EntraSSOError(409, "This app account is already linked to a different Microsoft identity.")
    user.entra_tenant_id = tenant_id
    user.entra_object_id = object_id


async def complete_sign_in(
    db: AsyncSession,
    *,
    state: str,
    code: str,
) -> EntraSignInResult:
    oauth_request = await _consume_oauth_request(db, state)
    id_token = await _exchange_code(code, oauth_request.code_verifier)
    claims = await _validate_id_token(id_token, oauth_request.nonce_digest)
    tenant_id, object_id, email, _ = _identity_fields(claims)
    if oauth_request.flow == "link":
        if oauth_request.user_id is None:
            raise EntraSSOError(400, "Microsoft account-link request was invalid. Try again.")
        user = await db.scalar(select(User).where(User.id == oauth_request.user_id))
        if user is None:
            raise EntraSSOError(401, "The app account for this link request no longer exists.")
        await _link_identity(
            db,
            user=user,
            tenant_id=tenant_id,
            object_id=object_id,
            email=email,
        )
        await db.commit()
        return EntraSignInResult(linked=True)
    if oauth_request.flow != "login":
        raise EntraSSOError(400, "Microsoft sign-in request was invalid. Try again.")

    user = await _find_or_create_user(db, claims)
    ticket = secrets.token_urlsafe(32)
    db.add(
        EntraLoginTicket(
            ticket_digest=_digest(ticket),
            user_id=user.id,
            expires_at=_now() + timedelta(minutes=1),
        )
    )
    await db.commit()
    return EntraSignInResult(ticket=ticket)


async def exchange_login_ticket(db: AsyncSession, ticket: str) -> TokenResponse:
    record = await db.scalar(
        select(EntraLoginTicket)
        .where(
            EntraLoginTicket.ticket_digest == _digest(ticket),
            EntraLoginTicket.expires_at > _now(),
        )
        .with_for_update()
    )
    if record is None:
        raise EntraSSOError(401, "Microsoft sign-in expired or was already used. Try again.")
    user = await db.scalar(select(User).where(User.id == record.user_id))
    await db.delete(record)
    if user is None:
        await db.commit()
        raise EntraSSOError(401, "Microsoft sign-in could not be matched to an app account.")
    await db.commit()
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        user=UserPublic.model_validate(user),
    )
