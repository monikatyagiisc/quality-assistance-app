import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from quality_assistance_agent.runner_service import runner_service
from quality_assistance_agent.schemas import AssistRequest, AssistResponse
from quality_assistance_agent.settings import settings

load_dotenv()

if settings.google_api_key:
    os.environ.setdefault("GOOGLE_API_KEY", settings.google_api_key)
if settings.openai_api_key:
    os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)

app = FastAPI(
    title="Quality Assistance Agent",
    description="Google ADK agent service for quality engineering assistance.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "agent"}


@app.post("/assist", response_model=AssistResponse)
async def assist(request: AssistRequest) -> AssistResponse:
    config_error = settings.validate_model_credentials()
    if config_error:
        raise HTTPException(status_code=503, detail=config_error)
    try:
        session_id, response = await runner_service.run(
            user_id=request.user_id,
            session_id=request.session_id,
            message=request.message,
        )
        return AssistResponse(session_id=session_id, response=response)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
