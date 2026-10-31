from __future__ import annotations

import base64
import hashlib
import unittest
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse
from unittest.mock import AsyncMock, patch
from uuid import UUID

import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt
from pydantic import SecretStr

from quality_assistance_backend.config import settings
from quality_assistance_backend.models import User
from quality_assistance_backend.services import entra_sso_service
from quality_assistance_backend.services.entra_sso_service import (
    EntraSSOError,
    _digest,
    _identity_fields,
    _validate_id_token,
    authorization_url,
)


TENANT_ID = "12345678-1234-5678-1234-567812345678"
CLIENT_ID = "client-id"


def _b64url_int(value: int) -> str:
    encoded = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(encoded).rstrip(b"=").decode("ascii")


class EntraSSOServiceTests(unittest.TestCase):
    def test_authorization_url_includes_tenant_and_pkce_challenge(self) -> None:
        verifier = "a" * 64
        with patch.multiple(
            settings,
            entra_tenant_id=TENANT_ID,
            entra_client_id=CLIENT_ID,
            entra_client_secret=SecretStr("client-secret"),
            entra_redirect_uri="http://localhost:8000/api/auth/entra/callback",
            entra_frontend_url="http://localhost:5173/login",
        ):
            url = authorization_url("state-value", "nonce-value", verifier)

        query = parse_qs(urlparse(url).query)
        expected_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")
        self.assertIn(f"/{TENANT_ID}/oauth2/v2.0/authorize", url)
        self.assertEqual(query["state"], ["state-value"])
        self.assertEqual(query["nonce"], ["nonce-value"])
        self.assertEqual(query["code_challenge"], [expected_challenge])
        self.assertEqual(query["code_challenge_method"], ["S256"])

    def test_identity_fields_require_valid_email_and_uuid_claims(self) -> None:
        identity = _identity_fields(
            {
                "tid": TENANT_ID,
                "oid": "87654321-4321-8765-4321-876543218765",
                "email": "Person@Example.com",
                "name": "Example Person",
            }
        )
        self.assertEqual(
            identity,
            (
                TENANT_ID,
                "87654321-4321-8765-4321-876543218765",
                "person@example.com",
                "Example Person",
            ),
        )
        with self.assertRaises(EntraSSOError):
            _identity_fields({"tid": TENANT_ID, "oid": str(UUID(int=1))})


class EntraIDTokenValidationTests(unittest.IsolatedAsyncioTestCase):
    async def test_existing_email_is_not_auto_linked_during_sso_login(self) -> None:
        existing_user = User(
            id=UUID(int=1),
            email="person@example.com",
            full_name="Person",
            password_hash="existing-password-hash",
        )
        db = AsyncMock()
        claims = {
            "tid": TENANT_ID,
            "oid": "87654321-4321-8765-4321-876543218765",
            "email": "person@example.com",
        }
        with (
            patch.object(
                entra_sso_service,
                "get_user_by_entra_identity",
                new=AsyncMock(return_value=None),
            ),
            patch.object(
                entra_sso_service,
                "get_user_by_email",
                new=AsyncMock(return_value=existing_user),
            ),
        ):
            with self.assertRaises(EntraSSOError) as error:
                await entra_sso_service._find_or_create_user(db, claims)
        self.assertEqual(error.exception.status_code, 409)
        db.add.assert_not_called()

    async def test_link_requires_same_email_as_authenticated_account(self) -> None:
        user = User(
            id=UUID(int=1),
            email="person@example.com",
            full_name="Person",
            password_hash="existing-password-hash",
        )
        with self.assertRaises(EntraSSOError) as error:
            await entra_sso_service._link_identity(
                AsyncMock(),
                user=user,
                tenant_id=TENANT_ID,
                object_id="87654321-4321-8765-4321-876543218765",
                email="different@example.com",
            )
        self.assertEqual(error.exception.status_code, 403)

    async def test_validates_signature_issuer_audience_tenant_and_nonce(self) -> None:
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_numbers = private_key.public_key().public_numbers()
        jwk_data = {
            "kty": "RSA",
            "use": "sig",
            "kid": "test-key",
            "n": _b64url_int(public_numbers.n),
            "e": _b64url_int(public_numbers.e),
        }
        nonce = "random-nonce"
        token = jwt.encode(
            {
                "iss": f"https://login.microsoftonline.com/{TENANT_ID}/v2.0",
                "aud": CLIENT_ID,
                "sub": "subject",
                "tid": TENANT_ID,
                "oid": "87654321-4321-8765-4321-876543218765",
                "email": "person@example.com",
                "nonce": nonce,
                "iat": datetime.now(timezone.utc),
                "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
            },
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            ),
            algorithm="RS256",
            headers={"kid": "test-key"},
        )
        transport = httpx.MockTransport(
            lambda request: httpx.Response(200, json={"keys": [jwk_data]})
        )
        real_async_client = httpx.AsyncClient

        def mock_async_client(**kwargs: object) -> httpx.AsyncClient:
            return real_async_client(transport=transport, **kwargs)

        with (
            patch.multiple(
                settings,
                entra_tenant_id=TENANT_ID,
                entra_client_id=CLIENT_ID,
                entra_client_secret=SecretStr("client-secret"),
                entra_redirect_uri="http://localhost:8000/api/auth/entra/callback",
                entra_frontend_url="http://localhost:5173/login",
            ),
            patch.object(entra_sso_service.httpx, "AsyncClient", side_effect=mock_async_client),
        ):
            claims = await _validate_id_token(token, _digest(nonce))
            self.assertEqual(claims["email"], "person@example.com")
            with self.assertRaises(EntraSSOError):
                await _validate_id_token(token, _digest("wrong-nonce"))
