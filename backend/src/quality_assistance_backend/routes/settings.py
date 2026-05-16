from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from quality_assistance_backend.db import get_db
from quality_assistance_backend.deps import get_current_user
from quality_assistance_backend.models import User
from quality_assistance_backend.schemas.settings import (
    FetchDiffInput,
    FetchDiffOutput,
    RepositoryConnectionInput,
    RepositoryConnectionPublic,
)
from quality_assistance_backend.services import repository_connection_service as repo_service

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/repository")
async def get_repository_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    connection = await repo_service.get_connection(db, current_user.id)
    if connection is None:
        return JSONResponse(content=None)
    return JSONResponse(content=repo_service.to_public(connection).model_dump())


@router.put("/repository", response_model=RepositoryConnectionPublic)
async def save_repository_settings(
    payload: RepositoryConnectionInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RepositoryConnectionPublic:
    try:
        return await repo_service.upsert_connection(db=db, user=current_user, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/repository", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await repo_service.delete_connection(db=db, user=current_user)


@router.post("/repository/fetch-diff", response_model=FetchDiffOutput)
async def fetch_repository_diff(
    payload: FetchDiffInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FetchDiffOutput:
    try:
        return await repo_service.fetch_diff(db=db, user=current_user, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
