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


@dataclass(frozen=True, slots=True)
class CrossFilingRevision:
    concept: str
    unit: str
    period_start: str | None
    period_end: str
    original_accession: str
    original_value: Decimal
    later_accession: str
    later_value: Decimal
    absolute_change: Decimal
    classification: str = "cross_filing_revision"


def compare_filing_facts(
    original: FilingFact, later: FilingFact
) -> CrossFilingRevision | None:
    """Compare the same economic fact without asserting a formal restatement."""
    identity = (
        original.taxonomy,
        original.concept,
        original.unit,
        original.period_start,
        original.period_end,
    )
    later_identity = (
        later.taxonomy,
        later.concept,
        later.unit,
        later.period_start,
        later.period_end,
    )
    if identity != later_identity:
        raise ValueError("Cross-filing comparison requires identical economic periods")
    if original.accession_number == later.accession_number:
        raise ValueError("Cross-filing comparison requires distinct accessions")
    if original.value == later.value:
        return None
    return CrossFilingRevision(
        concept=original.concept,
        unit=original.unit,
        period_start=original.period_start,
        period_end=original.period_end,
        original_accession=original.accession_number,
        original_value=original.value,
        later_accession=later.accession_number,
        later_value=later.value,
        absolute_change=later.value - original.value,
    )


def find_original_filing_fact(
    company_facts: dict[str, Any], *, later: FilingFact
) -> FilingFact | None:
    """Find the earliest prior 10-K observation for the same economic period."""
    try:
        observations = company_facts["facts"][later.taxonomy][later.concept]["units"][
            later.unit
        ]
    except (KeyError, TypeError):
        return None
    candidates = [
        item
        for item in observations
        if item.get("form") == "10-K"
        and item.get("accn") != later.accession_number
        and item.get("start") == later.period_start
        and item.get("end") == later.period_end
        and item.get("filed", "") < later.filed
    ]
    if not candidates:
        return None
    original = min(candidates, key=lambda item: (item["filed"], item["accn"]))
    return select_filing_fact(
        company_facts,
        taxonomy=later.taxonomy,
        concept=later.concept,
        unit=later.unit,
        accession_number=original["accn"],
        period_start=later.period_start,
        period_end=later.period_end,
    )


def select_filing_fact(
    company_facts: dict[str, Any],
    *,
    taxonomy: str,
    concept: str,
    unit: str,
    accession_number: str,
    period_start: str | None = None,
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
        and (period_start is None or observation.get("start") == period_start)
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


def list_filing_facts(
    company_facts: dict[str, Any],
    *,
    taxonomy: str,
    concept: str,
    unit: str,
    accession_number: str,
    form: str = "10-K",
) -> tuple[FilingFact, ...]:
    """List unambiguous periods exactly as presented in one filing accession."""
    try:
        concept_data = company_facts["facts"][taxonomy][concept]
        observations = concept_data["units"][unit]
    except (KeyError, TypeError) as error:
        raise XbrlFactError(f"Missing {taxonomy}:{concept} in unit {unit}") from error
    matching = [
        item
        for item in observations
        if item.get("accn") == accession_number and item.get("form") == form
    ]
    periods = {(item.get("start"), item.get("end")) for item in matching}
    facts = []
    for start, end in periods:
        facts.append(
            select_filing_fact(
                company_facts,
                taxonomy=taxonomy,
                concept=concept,
                unit=unit,
                accession_number=accession_number,
                period_start=start,
                period_end=end,
            )
        )
    return tuple(
        sorted(facts, key=lambda fact: (fact.period_end, fact.period_start or ""))
    )
