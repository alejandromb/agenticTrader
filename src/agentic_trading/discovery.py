"""Read-only discovery normalization; never ranks expected returns or trades."""

import argparse
import json
from datetime import date, timedelta
from pathlib import Path

from agentic_trading.artifacts import LocalArtifactStore


def normalize_calendar(rows: list, *, start: date, days: int) -> dict:
    """Preserve every row, quarantine ambiguities, and produce a research queue."""
    if not 1 <= days <= 31:
        raise ValueError("Forward window must be 1–31 days")
    end = start + timedelta(days=days - 1)
    groups = {}
    quarantined = []
    for index, row in enumerate(rows):
        try:
            symbol = row["symbol"]
            year, quarter = row["year"], row["quarter"]
            report = row["report"]
            day = date.fromisoformat(report["date"])
            if not isinstance(symbol, str) or not symbol.strip():
                raise ValueError("Missing symbol")
            if (
                type(year) is not int
                or type(quarter) is not int
                or quarter not in range(1, 5)
            ):
                raise ValueError("Invalid fiscal period")
            if not start <= day <= end:
                raise ValueError("Outside requested window")
            # Deliberately conservative heuristic, not a claim the source is wrong.
            if not start.year - 1 <= year <= start.year + 1:
                raise ValueError("Old/unusual fiscal year requires verification")
            if type(report["verified"]) is not bool:
                raise ValueError("Missing confirmation state")
            if report.get("timing") not in (None, "am", "pm"):
                raise ValueError("Unknown report timing")
            eps = row["eps"]
            if not isinstance(eps, dict) or "actual" not in eps:
                raise ValueError("Missing EPS state")
            key = (symbol.strip().upper(), year, quarter)
            groups.setdefault(key, []).append((index, row))
        except (TypeError, KeyError, ValueError) as error:
            quarantined.append({"index": index, "reason": str(error), "row": row})

    queue, duplicates = [], []
    for key, entries in sorted(groups.items()):
        canonical = {json.dumps(row, sort_keys=True) for _, row in entries}
        if len(canonical) > 1:
            quarantined.extend(
                {"index": i, "reason": "Conflicting event records", "row": row}
                for i, row in entries
            )
            continue
        index, row = entries[0]
        duplicates.extend({"index": i, "duplicate_of": index} for i, _ in entries[1:])
        reported = row["eps"]["actual"] is not None
        queue.append(
            {
                "symbol": key[0],
                "fiscal_year": key[1],
                "quarter": key[2],
                "date": row["report"]["date"],
                "timing": row["report"].get("timing"),
                "stage": "verify_results" if reported else "watch_event",
                "date_status": "broker_confirmed"
                if row["report"]["verified"]
                else "tentative",
                "source_row": index,
                "next_gate": (
                    "Verify issuer release, valuation and portfolio fit; "
                    "no trade signal"
                ),
            }
        )
    queue.sort(key=lambda r: (r["date"], r["symbol"], r["fiscal_year"], r["quarter"]))
    return {
        "window_start": str(start),
        "window_end": str(end),
        "input_count": len(rows),
        "queue": queue,
        "duplicates": duplicates,
        "quarantined": quarantined,
        "limitations": [
            "Broker discovery only; not issuer-verified due diligence.",
            "Actual EPS availability does not validate its GAAP/adjusted basis.",
            "No expected-return ranking, sizing, or order authorization.",
        ],
    }


def save_discovery(payload: dict, root: Path) -> str:
    """Archive raw input and deterministic output as one content-addressed object."""
    from datetime import datetime

    stamp = datetime.fromisoformat(payload["retrieved_at"].replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("Retrieval time requires timezone")
    result = normalize_calendar(
        payload["calendar_rows"],
        start=date.fromisoformat(payload["start_date"]),
        days=payload["days"],
    )
    document = {
        "schema_version": 1,
        "policy_version": "calendar-triage-v1",
        "input": payload,
        "result": result,
    }
    content = json.dumps(document, sort_keys=True, allow_nan=False).encode()
    return LocalArtifactStore(root).put(content).sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--artifacts", type=Path, default=Path("data/discovery"))
    args = parser.parse_args()
    print(save_discovery(json.loads(args.input.read_text()), args.artifacts))


if __name__ == "__main__":
    main()
