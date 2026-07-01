"""Deterministic research workflow states and transitions."""

from __future__ import annotations

from enum import StrEnum


class WorkflowState(StrEnum):
    DRAFT = "draft"
    COLLECTING_EVIDENCE = "collecting_evidence"
    EVIDENCE_READY = "evidence_ready"
    ANALYZING = "analyzing"
    CHALLENGING = "challenging"
    SYNTHESIZING = "synthesizing"
    VALIDATING = "validating"
    AWAITING_HUMAN_DISPOSITION = "awaiting_human_disposition"
    COMPLETE = "complete"
    FAILED = "failed"


FORWARD_TRANSITIONS: dict[WorkflowState, frozenset[WorkflowState]] = {
    WorkflowState.DRAFT: frozenset({WorkflowState.COLLECTING_EVIDENCE}),
    WorkflowState.COLLECTING_EVIDENCE: frozenset({WorkflowState.EVIDENCE_READY}),
    WorkflowState.EVIDENCE_READY: frozenset({WorkflowState.ANALYZING}),
    WorkflowState.ANALYZING: frozenset({WorkflowState.CHALLENGING}),
    WorkflowState.CHALLENGING: frozenset({WorkflowState.SYNTHESIZING}),
    WorkflowState.SYNTHESIZING: frozenset({WorkflowState.VALIDATING}),
    WorkflowState.VALIDATING: frozenset({WorkflowState.AWAITING_HUMAN_DISPOSITION}),
    WorkflowState.AWAITING_HUMAN_DISPOSITION: frozenset({WorkflowState.COMPLETE}),
    WorkflowState.COMPLETE: frozenset(),
    WorkflowState.FAILED: frozenset(),
}


def can_transition(current: WorkflowState, target: WorkflowState) -> bool:
    """Return whether *target* is a valid next state from *current*."""
    if target is WorkflowState.FAILED:
        return current not in {WorkflowState.COMPLETE, WorkflowState.FAILED}
    return target in FORWARD_TRANSITIONS[current]
