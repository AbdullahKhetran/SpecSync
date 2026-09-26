"""
routes.py — FastAPI route handlers.

Endpoints:
    GET  /api/health          — liveness check + provider name
    POST /api/plan/sprints    — PRD → SprintPlan + ValidationReport
    POST /api/plan/tickets    — sprint → TicketList + ValidationReport
"""

from __future__ import annotations

import json
import logging
import os

from fastapi import APIRouter, HTTPException

from .models import (
    SprintPlan,
    SprintsRequest,
    SprintsResponse,
    TicketList,
    TicketsRequest,
    TicketsResponse,
    ValidationReport,
)
from .validators import validate_sprint_plan, validate_ticket_list

logger = logging.getLogger(__name__)

router = APIRouter()

# Maximum PRD length (configurable via env; PRD §8.3)
_MAX_PRD_CHARS: int = int(os.environ.get("MAX_PRD_CHARS", 30_000))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_provider():
    """Lazily import and instantiate the configured LLM provider."""
    provider_name = os.environ.get("LLM_PROVIDER", "watsonx").lower()
    if provider_name == "watsonx":
        from .providers.watsonx import WatsonxProvider
        return WatsonxProvider()
    raise ValueError(f"Unknown LLM_PROVIDER: {provider_name!r}. Supported: watsonx")


def _load_prompt(filename: str) -> str:
    """Read a prompt file from backend/prompts/."""
    prompts_dir = os.path.join(os.path.dirname(__file__), "..", "prompts")
    path = os.path.join(prompts_dir, filename)
    with open(path, encoding="utf-8") as f:
        return f.read()


async def _call_llm_with_retry(
    provider,
    system_prompt: str,
    user_prompt: str,
    schema: dict,
) -> str:
    """
    Call the LLM once; on bad JSON, retry once with the error message appended.
    Raises HTTPException(502) if both attempts fail.
    """
    for attempt in (1, 2):
        try:
            raw = await provider.generate_json(system_prompt, user_prompt, schema)
            json.loads(raw)   # validate it parses — raises ValueError if not
            return raw
        except (ValueError, KeyError, Exception) as exc:
            if attempt == 1:
                logger.warning("LLM attempt 1 failed (%s), retrying with error context.", exc)
                user_prompt = (
                    f"{user_prompt}\n\n"
                    f"[RETRY] Your previous response was not valid JSON. "
                    f"Error: {exc}. "
                    f"Return only a valid JSON object matching the provided schema."
                )
            else:
                logger.error("LLM attempt 2 failed: %s", exc)
                raise HTTPException(
                    status_code=502,
                    detail="The AI model failed to return valid output after retry. Please try again.",
                )


# ---------------------------------------------------------------------------
# GET /api/health
# ---------------------------------------------------------------------------


@router.get("/health")
async def health():
    """Liveness check. Returns provider name but no secrets."""
    return {
        "status": "ok",
        "provider": os.environ.get("LLM_PROVIDER", "watsonx"),
    }


# ---------------------------------------------------------------------------
# POST /api/plan/sprints
# ---------------------------------------------------------------------------


@router.post("/plan/sprints", response_model=SprintsResponse)
async def plan_sprints(request: SprintsRequest) -> SprintsResponse:
    """Convert a PRD to a sprint plan with requirements and client questions."""
    prd = request.prd_markdown.strip()

    if not prd:
        raise HTTPException(status_code=400, detail="prd_markdown must not be empty.")
    if len(prd) > _MAX_PRD_CHARS:
        raise HTTPException(
            status_code=400,
            detail=f"prd_markdown exceeds the {_MAX_PRD_CHARS:,}-character limit.",
        )

    provider = _get_provider()
    system_prompt = _load_prompt("prd_to_sprints.md")
    schema = SprintPlan.model_json_schema()

    user_prompt = (
        f"JSON schema to follow:\n```json\n{json.dumps(schema, indent=2)}\n```\n\n"
        f"PRD to process:\n\n{prd}"
    )

    raw = await _call_llm_with_retry(provider, system_prompt, user_prompt, schema)
    plan = SprintPlan.model_validate_json(raw)
    validation = validate_sprint_plan(plan, prd)

    return SprintsResponse(plan=plan, validation=validation)


# ---------------------------------------------------------------------------
# POST /api/plan/tickets
# ---------------------------------------------------------------------------


@router.post("/plan/tickets", response_model=TicketsResponse)
async def plan_tickets(request: TicketsRequest) -> TicketsResponse:
    """Generate developer tickets for one sprint."""
    prd = request.prd_markdown.strip()

    if not prd:
        raise HTTPException(status_code=400, detail="prd_markdown must not be empty.")
    if len(prd) > _MAX_PRD_CHARS:
        raise HTTPException(
            status_code=400,
            detail=f"prd_markdown exceeds the {_MAX_PRD_CHARS:,}-character limit.",
        )

    # Verify the requested sprint exists in the provided plan
    sprint_ids = {s.id for s in request.plan.sprints}
    if request.sprint_id not in sprint_ids:
        raise HTTPException(
            status_code=400,
            detail=f"sprint_id {request.sprint_id!r} not found in the provided plan.",
        )

    provider = _get_provider()
    system_prompt = _load_prompt("sprint_to_tickets.md")
    schema = TicketList.model_json_schema()

    plan_json = request.plan.model_dump_json(indent=2)
    user_prompt = (
        f"JSON schema to follow:\n```json\n{json.dumps(schema, indent=2)}\n```\n\n"
        f"Sprint to generate tickets for: {request.sprint_id}\n\n"
        f"Full sprint plan (for context, do not duplicate other sprints):\n"
        f"```json\n{plan_json}\n```\n\n"
        f"Original PRD:\n\n{prd}"
    )

    raw = await _call_llm_with_retry(provider, system_prompt, user_prompt, schema)
    ticket_list = TicketList.model_validate_json(raw)
    validation = validate_ticket_list(ticket_list, request.plan)

    return TicketsResponse(tickets=ticket_list, validation=validation)
