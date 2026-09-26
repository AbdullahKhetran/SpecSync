"""
Pydantic v2 data models — single source of truth for all request/response shapes.

Rules:
  - Every field is explicitly typed and documented.
  - Enums enforce the allowed literals so validation errors are early and clear.
  - Frontend TypeScript types MUST mirror these exactly; notify Person C on any change.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Shared enums
# ---------------------------------------------------------------------------


class RequirementKind(str, Enum):
    functional = "functional"
    non_functional = "non_functional"


class TicketType(str, Enum):
    feature = "feature"
    task = "task"
    chore = "chore"
    spike = "spike"


class TicketArea(str, Enum):
    frontend = "frontend"
    backend = "backend"
    database = "database"
    devops = "devops"
    design = "design"
    qa = "qa"


class TicketSize(str, Enum):
    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"


class TicketPriority(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class IssueSeverity(str, Enum):
    warning = "warning"
    error = "error"


# ---------------------------------------------------------------------------
# Capability 1 — Sprint plan
# ---------------------------------------------------------------------------


class Project(BaseModel):
    """Top-level project metadata extracted from the PRD."""

    name: str = Field(..., description="Short project name.")
    summary: str = Field(
        ...,
        description="2–4 sentences describing the project in technical language.",
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="Explicit assumptions made while reading the PRD.",
    )


class Requirement(BaseModel):
    """A single extracted requirement, always traceable to the PRD source text."""

    id: Annotated[str, Field(pattern=r"^R\d+$")] = Field(
        ..., description="Sequential identifier, e.g. R1, R2."
    )
    text: str = Field(..., description="Requirement restated in technical language.")
    source_quote: str = Field(
        ..., description="Verbatim excerpt from the PRD that this requirement derives from."
    )
    kind: RequirementKind = Field(
        ..., description="Whether this is a functional or non-functional requirement."
    )


class Sprint(BaseModel):
    """One logical sprint (phase), grouping related requirements."""

    id: Annotated[str, Field(pattern=r"^S\d+$")] = Field(
        ..., description="Sequential identifier, e.g. S1, S2."
    )
    order: int = Field(..., ge=1, description="Execution order; lower runs first.")
    name: str = Field(..., description="Short sprint name.")
    goal: str = Field(..., description="One sentence describing the sprint outcome.")
    requirement_ids: list[Annotated[str, Field(pattern=r"^R\d+$")]] = Field(
        default_factory=list,
        description="Requirements addressed in this sprint.",
    )
    deliverables: list[str] = Field(
        default_factory=list,
        description="Concrete artefacts produced by this sprint.",
    )
    depends_on: list[Annotated[str, Field(pattern=r"^S\d+$")]] = Field(
        default_factory=list,
        description="Sprint IDs that must complete before this sprint can start.",
    )
    rationale: str = Field(
        ...,
        description="Why this work belongs here and in this order.",
    )


class ClientQuestion(BaseModel):
    """A clarifying question for the client, written in non-technical language."""

    id: Annotated[str, Field(pattern=r"^Q\d+$")] = Field(
        ..., description="Sequential identifier, e.g. Q1, Q2."
    )
    question: str = Field(
        ..., description="The question, written for a non-technical reader."
    )
    why_it_matters: str = Field(
        ..., description="Brief explanation of why the answer affects the plan."
    )
    requirement_ids: list[Annotated[str, Field(pattern=r"^R\d+$")]] = Field(
        default_factory=list,
        description="Requirements that depend on the answer to this question.",
    )


class SprintPlan(BaseModel):
    """Complete output of Capability 1 (POST /api/plan/sprints)."""

    project: Project
    requirements: list[Requirement] = Field(default_factory=list)
    sprints: list[Sprint] = Field(default_factory=list)
    client_questions: list[ClientQuestion] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Capability 2 — Ticket list
# ---------------------------------------------------------------------------


class Ticket(BaseModel):
    """A single developer-ready ticket within a sprint."""

    id: str = Field(
        ...,
        description="Unique ticket ID, e.g. S2-T1.",
        pattern=r"^S\d+-T\d+$",
    )
    title: str = Field(
        ...,
        max_length=100,
        description="Imperative title, max 100 characters.",
    )
    type: TicketType
    description: str = Field(..., description="Markdown description of the work.")
    acceptance_criteria: list[str] = Field(
        default_factory=list,
        description="Testable conditions that define done.",
    )
    technical_notes: str = Field(
        default="",
        description="Implementation hints, constraints, or links.",
    )
    areas: list[TicketArea] = Field(
        default_factory=list,
        description="Engineering disciplines this ticket touches.",
    )
    size: TicketSize
    priority: TicketPriority
    depends_on: list[str] = Field(
        default_factory=list,
        description="Ticket IDs within this sprint that must complete first.",
    )
    requirement_ids: list[Annotated[str, Field(pattern=r"^R\d+$")]] = Field(
        default_factory=list,
        description="Requirements this ticket satisfies.",
    )
    needs_clarification: bool = Field(
        default=False,
        description="True when this ticket is ambiguous or XL-sized.",
    )
    clarification_note: Optional[str] = Field(
        default=None,
        description="Explanation of what needs clarification; required when needs_clarification is True.",
    )

    @field_validator("needs_clarification", mode="before")
    @classmethod
    def xl_forces_clarification(cls, v: bool, info) -> bool:
        """XL tickets are always flagged for clarification (enforced at model level)."""
        size = (info.data or {}).get("size")
        if size == TicketSize.XL:
            return True
        return v


class TicketList(BaseModel):
    """Complete output of Capability 2 (POST /api/plan/tickets)."""

    sprint_id: Annotated[str, Field(pattern=r"^S\d+$")] = Field(
        ..., description="The sprint these tickets belong to."
    )
    tickets: list[Ticket] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Shared validation report (returned alongside every capability output)
# ---------------------------------------------------------------------------


class ValidationIssue(BaseModel):
    severity: IssueSeverity
    target: str = Field(..., description="The ID of the entity that has the issue (e.g. R3, S2-T1).")
    message: str


class ValidationReport(BaseModel):
    ok: bool = Field(..., description="True when there are no error-level issues.")
    issues: list[ValidationIssue] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# API request / response envelopes
# ---------------------------------------------------------------------------


class SprintsRequest(BaseModel):
    prd_markdown: str = Field(..., description="The full PRD text in Markdown.")


class SprintsResponse(BaseModel):
    plan: SprintPlan
    validation: ValidationReport


class TicketsRequest(BaseModel):
    prd_markdown: str = Field(..., description="The full PRD text in Markdown.")
    plan: SprintPlan = Field(..., description="Sprint plan, possibly edited by the user.")
    sprint_id: Annotated[str, Field(pattern=r"^S\d+$")] = Field(
        ..., description="The sprint to generate tickets for."
    )


class TicketsResponse(BaseModel):
    tickets: TicketList
    validation: ValidationReport
