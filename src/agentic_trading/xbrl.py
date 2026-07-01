"""Deterministic selection of SEC company-facts observations."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


class XbrlFactError(LookupError):
    """Raised when a requested filing fact is missing or ambiguous."""


@dataclass(frozen=True, slots=True)
class FilingFact:
    taxonomy: str
    concept: str
    label: str
    unit: str
    value: Decimal
    period_start: str | None
    period_end: str
    filed: str
    form: str
    accession_number: str
    fiscal_year: int | None
    fiscal_period: str | None


def select_filing_fact(
    company_facts: dict[str, Any],
    *,
    taxonomy: str,
    concept: str,
    unit: str,
    accession_number: str,
    period_end: str | None = None,
) -> FilingFact:
    """Select one fact observation tied to an exact SEC accession."""
    try:
        concept_data = company_facts["facts"][taxonomy][concept]
        observations = concept_data["units"][unit]
    except (KeyError, TypeError) as error:
        raise XbrlFactError(f"Missing {taxonomy}:{concept} in unit {unit}") from error

    matches = [
        observation
        for observation in observations
        if observation.get("accn") == accession_number
        and (period_end is None or observation.get("end") == period_end)
    ]
    if not matches:
        raise XbrlFactError(
            f"No {taxonomy}:{concept} observation for accession {accession_number}"
        )

    distinct = {
        (
            str(observation.get("val")),
            observation.get("start"),
            observation.get("end"),
            observation.get("form"),
            observation.get("fy"),
            observation.get("fp"),
        )
        for observation in matches
    }
    if len(distinct) != 1:
        raise XbrlFactError(
            f"Ambiguous {taxonomy}:{concept} observations for {accession_number}"
        )

    observation = matches[0]
    return FilingFact(
        taxonomy=taxonomy,
        concept=concept,
        label=concept_data.get("label", concept),
        unit=unit,
        value=Decimal(str(observation["val"])),
        period_start=observation.get("start"),
        period_end=observation["end"],
        filed=observation["filed"],
        form=observation["form"],
        accession_number=observation["accn"],
        fiscal_year=observation.get("fy"),
        fiscal_period=observation.get("fp"),
    )
