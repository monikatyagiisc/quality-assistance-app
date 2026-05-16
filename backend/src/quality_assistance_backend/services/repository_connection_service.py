from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from quality_assistance_backend.crypto.fernet_encryption import FernetEncryption
from quality_assistance_backend.models import RepositoryConnection, User
from quality_assistance_backend.schemas.settings import (
    FetchDiffInput,
    FetchDiffOutput,
    RepositoryConnectionInput,
    RepositoryConnectionPublic,
)
from quality_assistance_backend.services.github_diff_service import GitHubDiffService

_encryptor = FernetEncryption()


def to_public(connection: RepositoryConnection) -> RepositoryConnectionPublic:
    return RepositoryConnectionPublic(
        provider=connection.provider,
        owner=connection.owner,
        repo=connection.repo,
        default_branch=connection.default_branch,
        has_token=bool(connection.access_token_encrypted),
        repo_label=f"{connection.owner}/{connection.repo}",
    )


async def get_connection(
    db: AsyncSession,
    user_id,
) -> RepositoryConnection | None:
    result = await db.execute(
        select(RepositoryConnection).where(RepositoryConnection.user_id == user_id)
    )
    return result.scalar_one_or_none()


def decrypt_token(connection: RepositoryConnection) -> str | None:
    if not connection.access_token_encrypted:
        return None
    return _encryptor.decrypt(connection.access_token_encrypted)


async def upsert_connection(
    *,
    db: AsyncSession,
    user: User,
    payload: RepositoryConnectionInput,
) -> RepositoryConnectionPublic:
    connection = await get_connection(db, user.id)

    if connection is None:
        connection = RepositoryConnection(user_id=user.id)
        db.add(connection)

    connection.provider = payload.provider
    connection.owner = payload.owner
    connection.repo = payload.repo
    connection.default_branch = payload.default_branch

    has_existing_token = bool(connection.access_token_encrypted)
    if payload.access_token:
        connection.access_token_encrypted = _encryptor.encrypt(payload.access_token.strip())
    elif not has_existing_token:
        raise ValueError(
            "Personal access token is required. Add a GitHub PAT with repository read access."
        )

    await db.commit()
    await db.refresh(connection)
    return to_public(connection)


async def delete_connection(*, db: AsyncSession, user: User) -> None:
    connection = await get_connection(db, user.id)
    if connection is None:
        return
    await db.delete(connection)
    await db.commit()


async def fetch_diff(
    *,
    db: AsyncSession,
    user: User,
    payload: FetchDiffInput,
) -> FetchDiffOutput:
    connection = await get_connection(db, user.id)
    if connection is None:
        raise ValueError("No repository configured. Add owner, repo, and PAT in Settings first.")

    token = decrypt_token(connection)
    if not token:
        raise ValueError(
            "A personal access token is required to fetch diffs. Add a PAT in Settings."
        )

    client = GitHubDiffService(owner=connection.owner, repo=connection.repo, token=token)

    if payload.pull_number is not None:
        diff, summary = await client.fetch_pull_diff(payload.pull_number)
        source = f"github:pr:{payload.pull_number}"
    else:
        if not payload.head:
            raise ValueError("Provide a head branch/SHA or a pull request number.")
        base = payload.base or connection.default_branch
        diff, summary = await client.fetch_compare_diff(base, payload.head)
        source = f"github:compare:{base}...{payload.head}"

    return FetchDiffOutput(diff=diff, source=source, summary=summary)
