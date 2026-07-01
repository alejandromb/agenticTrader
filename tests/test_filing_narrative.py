from agentic_trading.filing_narrative import extract_capital_allocation_statements


def test_extracts_deduplicated_capital_spending_purpose() -> None:
    statement = (
        "Capital expenditures increased by $2.9 billion to support our "
        "omnichannel growth strategy."
    )
    html = f"<html><p>{statement}</p><div>{statement}</div></html>".encode()

    assert extract_capital_allocation_statements(html) == (statement,)


def test_rejects_capex_value_without_stated_purpose() -> None:
    html = b"<html><p>Capital expenditures were $26.6 billion.</p></html>"

    assert extract_capital_allocation_statements(html) == ()


def test_rejects_market_risk_boilerplate() -> None:
    html = b"""<html><p>A failure to meet market expectations for capital
    expenditures and growth initiatives could cause our stock price to decline.
    </p></html>"""

    assert extract_capital_allocation_statements(html) == ()
