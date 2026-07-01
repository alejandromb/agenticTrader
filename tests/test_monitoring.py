import json
from pathlib import Path

import pytest

from agentic_trading.disposition_repository import SqliteDispositionRepository
from agentic_trading.market_data import SqlitePriceDatasetRepository
from agentic_trading.migrations import upgrade_database
from agentic_trading.monitoring import MonitoringError, SqliteDecisionMonitoring
from agentic_trading.repository import SqliteRunRepository
from agentic_trading.workflow import WorkflowState

FIXTURES = Path(__file__).parent / "fixtures"


def completed_run(database: Path, disposition: str = "watch") -> str:
    runs = SqliteRunRepository(database)
    run = runs.create_run(memo_id="memo-monitor", as_of="2025-01-01T00:00:00Z")
    for target in (
        WorkflowState.COLLECTING_EVIDENCE,
        WorkflowState.EVIDENCE_READY,
        WorkflowState.ANALYZING,
        WorkflowState.CHALLENGING,
        WorkflowState.SYNTHESIZING,
        WorkflowState.VALIDATING,
        WorkflowState.AWAITING_HUMAN_DISPOSITION,
    ):
        run = runs.transition(run.run_id, expected_state=run.state, target_state=target)
    SqliteDispositionRepository(database).record(
        run_id=run.run_id, status=disposition, rationale="Fixture decision"
    )
    runs.transition(
        run.run_id, expected_state=run.state, target_state=WorkflowState.COMPLETE
    )
    return run.run_id


def setup_monitoring(tmp_path, disposition: str = "watch"):
    database = tmp_path / "state.db"
    artifacts = tmp_path / "artifacts"
    upgrade_database(database)
    run_id = completed_run(database, disposition)
    dataset = SqlitePriceDatasetRepository(database, artifacts).import_csv(
        FIXTURES / "prices-valid.csv", source="Monitoring fixture"
    )
    service = SqliteDecisionMonitoring(database, artifacts)
    return service, run_id, dataset


def test_monitor_creation_requires_eligible_human_disposition(tmp_path) -> None:
    service, run_id, _ = setup_monitoring(tmp_path)

    monitor = service.create_monitor(
        run_id=run_id,
        name="Apple follow-up",
        rules_path=FIXTURES / "monitor-rules.json",
    )

    assert monitor.run_id == run_id
    assert len(monitor.rules) == 3
    assert (
        Path(monitor.rules_storage_path).read_bytes()
        == (FIXTURES / "monitor-rules.json").read_bytes()
    )
    assert service.get_monitor(monitor.monitor_id) == monitor


def test_rejected_disposition_is_ineligible(tmp_path) -> None:
    service, run_id, _ = setup_monitoring(tmp_path, disposition="reject")

    with pytest.raises(MonitoringError, match="watch or consider_for_portfolio"):
        service.create_monitor(
            run_id=run_id,
            name="Ineligible",
            rules_path=FIXTURES / "monitor-rules.json",
        )


def test_evaluation_is_as_of_bounded_idempotent_and_creates_unique_alerts(
    tmp_path,
) -> None:
    service, run_id, dataset = setup_monitoring(tmp_path)
    monitor = service.create_monitor(
        run_id=run_id,
        name="Apple follow-up",
        rules_path=FIXTURES / "monitor-rules.json",
    )

    evaluation = service.evaluate(
        monitor.monitor_id, dataset_id=dataset.dataset_id, as_of="2025-01-06"
    )
    repeated = service.evaluate(
        monitor.monitor_id, dataset_id=dataset.dataset_id, as_of="2025-01-06"
    )

    assert repeated == evaluation
    by_rule = {result["rule_id"]: result for result in evaluation.results}
    assert by_rule["price-floor"]["triggered"] is True
    assert by_rule["material-drawdown"]["triggered"] is True
    assert by_rule["strict-equality"]["triggered"] is False
    assert by_rule["price-floor"]["observation_date"] == "2025-01-06"
    alerts = service.list_alerts(monitor_id=monitor.monitor_id)
    assert len(alerts) == 2
    assert {alert.rule_id for alert in alerts} == {
        "price-floor",
        "material-drawdown",
    }


def test_as_of_boundary_excludes_later_observations(tmp_path) -> None:
    service, run_id, dataset = setup_monitoring(tmp_path)
    monitor = service.create_monitor(
        run_id=run_id,
        name="Boundary",
        rules_path=FIXTURES / "monitor-rules.json",
    )

    evaluation = service.evaluate(
        monitor.monitor_id, dataset_id=dataset.dataset_id, as_of="2025-01-03"
    )

    by_rule = {result["rule_id"]: result for result in evaluation.results}
    assert by_rule["price-floor"]["observed"] == "101.50"
    assert by_rule["price-floor"]["triggered"] is False
    assert by_rule["material-drawdown"]["observed"] == "0"


def test_acknowledgement_is_append_only_and_status_is_derived(tmp_path) -> None:
    service, run_id, dataset = setup_monitoring(tmp_path)
    monitor = service.create_monitor(
        run_id=run_id,
        name="Acknowledgement",
        rules_path=FIXTURES / "monitor-rules.json",
    )
    service.evaluate(
        monitor.monitor_id, dataset_id=dataset.dataset_id, as_of="2025-01-06"
    )
    alert = service.list_alerts(status="open")[0]

    acknowledgement = service.acknowledge(alert.alert_id, note="Reviewed by human")

    assert acknowledgement.alert_id == alert.alert_id
    assert not service.list_alerts(status="open") or all(
        item.alert_id != alert.alert_id for item in service.list_alerts(status="open")
    )
    assert alert.alert_id in {
        item.alert_id for item in service.list_alerts(status="acknowledged")
    }
    with pytest.raises(MonitoringError, match="already acknowledged"):
        service.acknowledge(alert.alert_id, note="Second acknowledgement")


@pytest.mark.parametrize(
    ("rules", "message"),
    [
        ([], "nonempty array"),
        (
            [
                {
                    "rule_id": "bad",
                    "type": "sentiment",
                    "ticker": "AAPL",
                    "threshold": "1",
                }
            ],
            "Unsupported rule type",
        ),
        (
            [
                {
                    "rule_id": "bad",
                    "type": "drawdown_at_least",
                    "ticker": "AAPL",
                    "threshold": "1.1",
                }
            ],
            "must not exceed one",
        ),
    ],
)
def test_invalid_rules_fail_explicitly(tmp_path, rules, message) -> None:
    service, run_id, _ = setup_monitoring(tmp_path)
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(rules))

    with pytest.raises(MonitoringError, match=message):
        service.create_monitor(run_id=run_id, name="Invalid", rules_path=path)
