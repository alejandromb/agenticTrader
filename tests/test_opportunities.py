from uuid import uuid4

import pytest
from pydantic import ValidationError

from agentic_trading.migrations import upgrade_database
from agentic_trading.opportunities import OpportunityDecision, OpportunityLedger


@pytest.fixture
def ledger(tmp_path):
    path = tmp_path / "state.db"
    upgrade_database(path)
    return OpportunityLedger(path)


def decision(**kwargs):
    return OpportunityDecision(
        **(
            dict(
                event_id=uuid4(),
                candidate_id=uuid4(),
                sequence=0,
                symbol="ABC",
                stage="discovered",
                recorded_at="2026-09-10T12:00:00Z",
                reason="Pilot",
                evidence_refs=["discovery:fixture"],
                limitations=["Not verified"],
            )
            | kwargs
        )
    )


def test_history_replay_and_reopen(ledger):
    first = decision()
    ledger.append(first)
    ledger.append(first)
    for seq, stage in enumerate(
        ["researching", "valuation", "rejected", "researching"], 1
    ):
        ledger.append(
            decision(candidate_id=first.candidate_id, sequence=seq, stage=stage)
        )
    assert len(ledger.history(first.candidate_id)) == 5
    assert ledger.latest()[0]["stage"] == "researching"


@pytest.mark.parametrize(
    "changes",
    [
        {"sequence": 0, "stage": "researching"},
        {"sequence": 1, "stage": "valuation"},
        {"sequence": 1, "stage": "researching", "symbol": "XYZ"},
        {"sequence": 1, "stage": "researching", "recorded_at": "2026-09-09T12:00:00Z"},
    ],
)
def test_invalid_transition_preserves_history(ledger, changes):
    first = decision()
    ledger.append(first)
    with pytest.raises(ValueError):
        ledger.append(decision(candidate_id=first.candidate_id, **changes))
    assert len(ledger.history(first.candidate_id)) == 1


def test_event_id_collision(ledger):
    first = decision()
    ledger.append(first)
    with pytest.raises(ValueError):
        ledger.append(first.model_copy(update={"reason": "Changed"}))


def test_first_event_must_be_discovery(ledger):
    with pytest.raises(ValueError):
        ledger.append(decision(stage="valuation"))


@pytest.mark.parametrize(
    "changes",
    [
        {"reason": " "},
        {"evidence_refs": []},
        {"limitations": []},
        {"stage": "approved"},
        {"recorded_at": "2026-09-10T12:00:00"},
    ],
)
def test_required_audit_fields(changes):
    with pytest.raises(ValidationError):
        decision(**changes)


def test_stale_writer_cannot_overwrite(ledger):
    first = decision()
    ledger.append(first)
    ledger.append(
        decision(candidate_id=first.candidate_id, sequence=1, stage="researching")
    )
    with pytest.raises(ValueError):
        ledger.append(
            decision(candidate_id=first.candidate_id, sequence=1, stage="rejected")
        )
    assert ledger.latest()[0]["stage"] == "researching"


def test_dashboard_evidence_integrity_and_no_path_reads(ledger, tmp_path):
    from agentic_trading.artifacts import LocalArtifactStore
    from agentic_trading.briefing import render_briefing

    store = LocalArtifactStore(tmp_path / "artifacts")
    artifact = store.put(b"source snapshot")
    first = decision(
        reason="<script>bad</script>",
        evidence_refs=["sha256:" + artifact.sha256, "../../.env", "sha256:" + "a" * 64],
    )
    ledger.append(first)
    records = ledger.dashboard_records(tmp_path / "artifacts")
    checks = records[0]["history"][0]["evidence_checks"]
    assert checks[0]["status"] == "content hash verified; claims not verified"
    assert checks[1]["status"] == "unresolved reference"
    assert checks[2]["status"] == "missing or corrupt artifact"
    html = render_briefing(tmp_path / "absent.json", candidate_records=records).decode()
    assert "&lt;script&gt;" in html
    assert "<script>" not in html
    assert "Candidate decision history" in html
    artifact.path.write_bytes(b"changed")
    assert (
        ledger.dashboard_records(tmp_path / "artifacts")[0]["history"][0][
            "evidence_checks"
        ][0]["status"]
        == "missing or corrupt artifact"
    )
