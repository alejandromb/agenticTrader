"""Durable research queue decisions, with no execution/approval states."""

import argparse
import json
from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from agentic_trading.database import create_sqlite_engine
from agentic_trading.models import OpportunityEventModel


class OpportunityDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    event_id: UUID
    candidate_id: UUID
    sequence: int = Field(ge=0)
    symbol: str = Field(pattern=r"^[A-Z][A-Z0-9.\-]{0,14}$")
    stage: Literal["discovered", "researching", "valuation", "deferred", "rejected"]
    recorded_at: AwareDatetime
    reason: str = Field(min_length=1)
    evidence_refs: list[str] = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)


class OpportunityLedger:
    def __init__(self, database: Path):
        self.sessions = sessionmaker(create_sqlite_engine(database))

    def append(self, event: OpportunityDecision):
        event = OpportunityDecision.model_validate_json(event.model_dump_json())
        if any(not s.strip() for s in event.evidence_refs + event.limitations):
            raise ValueError("Evidence and limitation entries must not be blank")
        serialized = event.model_dump_json()
        try:
            with self.sessions.begin() as session:
                existing = session.get(OpportunityEventModel, str(event.event_id))
                if existing:
                    if existing.record_json != serialized:
                        raise ValueError("Event ID reused with different content")
                    return  # Idempotent replay, not a new decision.
                previous = session.scalar(
                    select(OpportunityEventModel)
                    .where(
                        OpportunityEventModel.candidate_id == str(event.candidate_id)
                    )
                    .order_by(OpportunityEventModel.sequence.desc())
                    .limit(1)
                )
                if previous is None:
                    if event.sequence != 0 or event.stage != "discovered":
                        raise ValueError(
                            "Candidate must begin at discovered sequence 0"
                        )
                else:
                    prior = OpportunityDecision.model_validate_json(
                        previous.record_json
                    )
                    if event.sequence != prior.sequence + 1:
                        raise ValueError(
                            "Stale sequence; read latest history before retrying"
                        )
                    if (
                        event.symbol != prior.symbol
                        or event.recorded_at < prior.recorded_at
                    ):
                        raise ValueError(
                            "Symbol changed or decision time moved backwards"
                        )
                    allowed = {
                        "discovered": {"researching", "deferred", "rejected"},
                        "researching": {"valuation", "deferred", "rejected"},
                        "valuation": {"researching", "deferred", "rejected"},
                        "deferred": {"researching", "rejected"},
                        "rejected": {"researching"},
                    }
                    if event.stage not in allowed[prior.stage]:
                        raise ValueError("Invalid research stage transition")
                session.add(
                    OpportunityEventModel(
                        event_id=str(event.event_id),
                        candidate_id=str(event.candidate_id),
                        sequence=event.sequence,
                        record_json=serialized,
                    )
                )
        except IntegrityError as error:
            raise ValueError("Concurrent decision conflict; reload history") from error

    def history(self, candidate_id: UUID):
        with self.sessions() as session:
            rows = session.scalars(
                select(OpportunityEventModel)
                .where(OpportunityEventModel.candidate_id == str(candidate_id))
                .order_by(OpportunityEventModel.sequence)
            ).all()
            return [json.loads(row.record_json) for row in rows]

    def latest(self):
        with self.sessions() as session:
            rows = session.scalars(
                select(OpportunityEventModel).order_by(
                    OpportunityEventModel.candidate_id, OpportunityEventModel.sequence
                )
            ).all()
            latest = {row.candidate_id: json.loads(row.record_json) for row in rows}
            return sorted(
                latest.values(), key=lambda item: (item["symbol"], item["candidate_id"])
            )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database", type=Path, default=Path("data/agentic-trading.db")
    )
    parser.add_argument("--append", type=Path)
    parser.add_argument("--history", type=UUID)
    args = parser.parse_args()
    ledger = OpportunityLedger(args.database)
    if args.append:
        ledger.append(OpportunityDecision.model_validate_json(args.append.read_text()))
    print(
        json.dumps(
            ledger.history(args.history) if args.history else ledger.latest(), indent=2
        )
    )


if __name__ == "__main__":
    main()
