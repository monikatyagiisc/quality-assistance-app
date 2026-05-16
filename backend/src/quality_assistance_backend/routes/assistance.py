from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from quality_assistance_backend.db import get_db
from quality_assistance_backend.deps import get_current_user
from quality_assistance_backend.models import User
from quality_assistance_backend.schemas import AssistanceInput, AssistanceOutput
from quality_assistance_backend.services.assistance_service import run_assistance

router = APIRouter(prefix="/api", tags=["assistance"])


@router.post("/assist", response_model=AssistanceOutput)
async def assist(
    payload: AssistanceInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AssistanceOutput:
    return await run_assistance(db=db, current_user=current_user, payload=payload)
