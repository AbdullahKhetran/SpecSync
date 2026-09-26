"""
validators.py — deterministic post-LLM validation.

Runs on every LLM response BEFORE it is returned to the frontend.
Returns a ValidationReport; never raises — all issues are collected and reported.

Capability 1 rules  (PRD §7.4):
  1. source_quote appears in the PRD (normalised match; failures are warnings, not errors)
  2. Every requirement is assigned to at least one sprint
  3. Every requirement_ids entry in sprints/questions refers to an existing requirement
  4. Sprint depends_on: references exist, no cycle, no sprint depends on a higher-order sprint

Capability 2 rules  (PRD §7.4):
  1. Every ticket's requirement_ids belongs to the chosen sprint
  2. Every sprint requirement is covered by at least one ticket
  3. Ticket IDs are unique within the sprint
  4. depends_on references exist within the sprint and contain no cycle
  5. Any XL ticket is marked needs_clarification (already enforced by the model; re-checked here)
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from typing import List

from .models import (
    IssueSeverity,
    SprintPlan,
    TicketList,
    TicketSize,
    ValidationIssue,
    ValidationReport,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _normalise(text: str) -> str:
    """Lower-case, collapse whitespace, strip punctuation for fuzzy quote matching."""
    text = unicodedata.normalize("NFKD", text)
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _has_cycle(graph: dict[str, list[str]]) -> bool:
    """Return True if the directed graph (id -> [dependency ids]) contains a cycle."""
    WHITE, GRAY, BLACK = 0, 1, 2
    colour: dict[str, int] = defaultdict(int)

    def dfs(node: str) -> bool:
        colour[node] = GRAY
        for neighbour in graph.get(node, []):
            if colour[neighbour] == GRAY:
                return True
            if colour[neighbour] == WHITE and dfs(neighbour):
                return True
        colour[node] = BLACK
        return False

    for node in graph:
        if colour[node] == WHITE and dfs(node):
            return True
    return False


def _issue(severity: IssueSeverity, target: str, message: str) -> ValidationIssue:
    return ValidationIssue(severity=severity, target=target, message=message)


# ---------------------------------------------------------------------------
# Capability 1 — validate_sprint_plan
# ---------------------------------------------------------------------------


def validate_sprint_plan(plan: SprintPlan, prd_markdown: str) -> ValidationReport:
    """Run all Capability-1 validation rules and return a ValidationReport."""
    issues: List[ValidationIssue] = []
    norm_prd = _normalise(prd_markdown)
    req_ids = {r.id for r in plan.requirements}

    # Rule 1 — source_quote traceability
    for req in plan.requirements:
        norm_quote = _normalise(req.source_quote)
        if norm_quote and norm_quote not in norm_prd:
            issues.append(
                _issue(
                    IssueSeverity.warning,
                    req.id,
                    f'source_quote not found in PRD: "{req.source_quote[:80]}..."',
                )
            )

    # Rule 2 — every requirement covered by at least one sprint
    covered_req_ids: set[str] = set()
    for sprint in plan.sprints:
        covered_req_ids.update(sprint.requirement_ids)

    for req in plan.requirements:
        if req.id not in covered_req_ids:
            issues.append(
                _issue(
                    IssueSeverity.warning,
                    req.id,
                    f"Requirement {req.id} is not assigned to any sprint.",
                )
            )

    # Rule 3a — sprint requirement_ids reference existing requirements
    for sprint in plan.sprints:
        for rid in sprint.requirement_ids:
            if rid not in req_ids:
                issues.append(
                    _issue(
                        IssueSeverity.error,
                        sprint.id,
                        f"Sprint {sprint.id} references unknown requirement {rid}.",
                    )
                )

    # Rule 3b — client_question requirement_ids reference existing requirements
    for q in plan.client_questions:
        for rid in q.requirement_ids:
            if rid not in req_ids:
                issues.append(
                    _issue(
                        IssueSeverity.error,
                        q.id,
                        f"Question {q.id} references unknown requirement {rid}.",
                    )
                )

    # Rule 4 — sprint depends_on: references exist, no cycle, no forward dependency
    sprint_by_id = {s.id: s for s in plan.sprints}
    dep_graph: dict[str, list[str]] = {}

    for sprint in plan.sprints:
        dep_graph[sprint.id] = list(sprint.depends_on)
        for dep_id in sprint.depends_on:
            if dep_id not in sprint_by_id:
                issues.append(
                    _issue(
                        IssueSeverity.error,
                        sprint.id,
                        f"Sprint {sprint.id} depends_on unknown sprint {dep_id}.",
                    )
                )
            else:
                dep_sprint = sprint_by_id[dep_id]
                if dep_sprint.order >= sprint.order:
                    issues.append(
                        _issue(
                            IssueSeverity.error,
                            sprint.id,
                            (
                                f"Sprint {sprint.id} (order={sprint.order}) depends on "
                                f"{dep_id} (order={dep_sprint.order}), which has equal "
                                f"or higher order — dependency must point backwards."
                            ),
                        )
                    )

    if _has_cycle(dep_graph):
        issues.append(
            _issue(
                IssueSeverity.error,
                "sprints",
                "Sprint depends_on graph contains a cycle.",
            )
        )

    ok = not any(i.severity == IssueSeverity.error for i in issues)
    return ValidationReport(ok=ok, issues=issues)


# ---------------------------------------------------------------------------
# Capability 2 — validate_ticket_list
# ---------------------------------------------------------------------------


def validate_ticket_list(
    ticket_list: TicketList,
    plan: SprintPlan,
) -> ValidationReport:
    """Run all Capability-2 validation rules and return a ValidationReport."""
    issues: List[ValidationIssue] = []

    # Locate the sprint in the plan
    sprint = next((s for s in plan.sprints if s.id == ticket_list.sprint_id), None)
    if sprint is None:
        return ValidationReport(
            ok=False,
            issues=[
                _issue(
                    IssueSeverity.error,
                    ticket_list.sprint_id,
                    f"Sprint {ticket_list.sprint_id} not found in the provided plan.",
                )
            ],
        )

    sprint_req_ids = set(sprint.requirement_ids)
    ticket_ids = [t.id for t in ticket_list.tickets]

    # Rule 3 — ticket IDs unique
    seen_ids: set[str] = set()
    for tid in ticket_ids:
        if tid in seen_ids:
            issues.append(
                _issue(
                    IssueSeverity.error,
                    tid,
                    f"Duplicate ticket ID: {tid}.",
                )
            )
        seen_ids.add(tid)

    ticket_id_set = set(ticket_ids)
    covered_sprint_reqs: set[str] = set()

    for ticket in ticket_list.tickets:
        # Rule 1 — ticket requirement_ids belong to this sprint
        for rid in ticket.requirement_ids:
            if rid not in sprint_req_ids:
                issues.append(
                    _issue(
                        IssueSeverity.error,
                        ticket.id,
                        (
                            f"Ticket {ticket.id} references requirement {rid} "
                            f"which is not in sprint {ticket_list.sprint_id}."
                        ),
                    )
                )
            else:
                covered_sprint_reqs.add(rid)

        # Rule 4 — depends_on references exist within the sprint
        for dep_id in ticket.depends_on:
            if dep_id not in ticket_id_set:
                issues.append(
                    _issue(
                        IssueSeverity.error,
                        ticket.id,
                        f"Ticket {ticket.id} depends_on unknown ticket {dep_id}.",
                    )
                )

        # Rule 5 — XL tickets must have needs_clarification=True
        if ticket.size == TicketSize.XL and not ticket.needs_clarification:
            issues.append(
                _issue(
                    IssueSeverity.error,
                    ticket.id,
                    f"Ticket {ticket.id} is XL-sized but needs_clarification is False.",
                )
            )

    # Rule 2 — every sprint requirement covered by at least one ticket
    for rid in sprint_req_ids:
        if rid not in covered_sprint_reqs:
            issues.append(
                _issue(
                    IssueSeverity.warning,
                    rid,
                    f"Requirement {rid} of sprint {ticket_list.sprint_id} is not covered by any ticket.",
                )
            )

    # Rule 4 continued — depends_on cycle check
    dep_graph: dict[str, list[str]] = {
        t.id: [d for d in t.depends_on if d in ticket_id_set]
        for t in ticket_list.tickets
    }
    if _has_cycle(dep_graph):
        issues.append(
            _issue(
                IssueSeverity.error,
                ticket_list.sprint_id,
                "Ticket depends_on graph contains a cycle.",
            )
        )

    ok = not any(i.severity == IssueSeverity.error for i in issues)
    return ValidationReport(ok=ok, issues=issues)
