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
    known_limitations: list[str] = Field(default_factory=list)
    business_quality: list[AnalysisPoint] = Field(default_factory=list)
    material_risks: list[AnalysisPoint] = Field(default_factory=list)
    bull_case: list[AnalysisPoint] = Field(default_factory=list)
    base_case: list[AnalysisPoint] = Field(default_factory=list)
    bear_case: list[AnalysisPoint] = Field(default_factory=list)
    devils_advocate: list[AnalysisPoint] = Field(default_factory=list)
    valuation: list[AnalysisPoint] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_content(self) -> FinancialAnalysis:
        if not (
            self.strengths
            or self.concerns
            or self.uncertainties
            or self.cash_allocation
            or self.trends
            or self.business_quality
            or self.material_risks
            or self.bull_case
            or self.base_case
            or self.bear_case
            or self.devils_advocate
            or self.valuation
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
                self.business_quality,
                self.material_risks,
                self.bull_case,
                self.base_case,
                self.bear_case,
                self.devils_advocate,
                self.valuation,
            )
            for point in group
            for claim_id in point.claim_ids
        }
