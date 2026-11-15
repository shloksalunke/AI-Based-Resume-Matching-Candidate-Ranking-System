from fastapi import APIRouter
from app.core.config import settings
from app.schemas.llm import LlmStatusResponse
from app.services.llm_service import is_llm_enabled

router = APIRouter(prefix="/llm", tags=["LLM"])


@router.get("/status", response_model=LlmStatusResponse)
def get_llm_status():
    """Returns whether the optional LLM layer is enabled and the max candidate evaluation limit."""
    return LlmStatusResponse(
        enabled=is_llm_enabled(),
        max_candidates=settings.LLM_MAX_CANDIDATES,
    )
