from pathlib import Path

import pytest

from agentic_trading.market_data import (
    PriceDatasetError,
    SqlitePriceDatasetRepository,
)
from agentic_trading.migrations import upgrade_database

FIXTURE = Path(__file__).parent / "fixtures/prices-valid.csv"


def repository(tmp_path):
    database = tmp_path / "state.db"
    upgrade_database(database)
    return SqlitePriceDatasetRepository(database, tmp_path / "artifacts")


def test_import_is_immutable_retrievable_and_content_addressed(tmp_path) -> None:
    prices = repository(tmp_path)

    dataset = prices.import_csv(FIXTURE, source="Test fixture")
    repeated = prices.import_csv(FIXTURE, source="Test fixture")

    assert repeated == dataset
    assert dataset.row_count == 6
    assert dataset.start_date == "2025-01-02"
    assert dataset.end_date == "2025-01-06"
    assert Path(dataset.storage_path).read_bytes() == FIXTURE.read_bytes()
    assert len(prices.observations(dataset.dataset_id)) == 6
    assert prices.list_datasets() == (dataset,)


def test_import_bytes_preserves_exact_payload(tmp_path) -> None:
    prices = repository(tmp_path)
    payload = FIXTURE.read_bytes()

    dataset = prices.import_bytes(payload, source="Browser upload")

    assert Path(dataset.storage_path).read_bytes() == payload
    assert prices.import_bytes(payload, source="Repeated upload") == dataset


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (
            "ticker,date,adjusted_close\nAAPL,2025-01-02,100\nAAPL,2025-01-02,101\n",
            "Duplicate observation",
        ),
        (
            "ticker,date,adjusted_close\nAAPL,2025-01-03,100\nAAPL,2025-01-02,101\n",
            "Dates must increase strictly",
        ),
        ("ticker,date,adjusted_close\nAAPL,2025-01-02,-1\n", "must be positive"),
        ("ticker,date\nAAPL,2025-01-02\n", "requires ticker,date,adjusted_close"),
    ],
)
def test_invalid_price_data_fails_explicitly(
    tmp_path, payload: str, message: str
) -> None:
    path = tmp_path / "invalid.csv"
    path.write_text(payload)

    with pytest.raises(PriceDatasetError, match=message):
        repository(tmp_path).import_csv(path, source="Invalid fixture")
