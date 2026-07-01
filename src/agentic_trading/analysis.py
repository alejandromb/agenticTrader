"""Strict contracts for model-generated financial analysis."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AnalysisPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)
    claim_ids: list[str] = Field(min_length=1)


class FinancialAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assessment: Literal["positive", "mixed", "negative", "insufficient"]
    summary: str = Field(min_length=1)
    strengths: list[AnalysisPoint]
    concerns: list[AnalysisPoint]
    uncertainties: list[AnalysisPoint]
    cash_allocation: list[AnalysisPoint] = Field(default_factory=list)
    trends: list[AnalysisPoint] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_content(self) -> FinancialAnalysis:
        if not (
            self.strengths
            or self.concerns
            or self.uncertainties
            or self.cash_allocation
            or self.trends
        ):
            raise ValueError("analysis must contain at least one analytical point")
        return self

    def referenced_claim_ids(self) -> set[str]:
        return {
            claim_id
            for group in (
                self.strengths,
                self.concerns,
                self.uncertainties,
                self.cash_allocation,
                self.trends,
            )
            for point in group
            for claim_id in point.claim_ids
        }
