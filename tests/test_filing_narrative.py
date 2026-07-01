from agentic_trading.filing_narrative import (
    extract_capital_allocation_statements,
    extract_capital_allocation_table_details,
)


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


def test_extracts_quantified_capital_allocation_table_rows() -> None:
    html = b"""<table>
      <tr><td>Supply chain, technology and customer-facing initiatives</td>
          <td>$</td><td>16,468</td></tr>
      <tr><td>Store and club remodels</td><td>$</td><td>5,571</td></tr>
      <tr><td>Unrelated tax expense</td><td>$</td><td>100</td></tr>
    </table>"""

    assert extract_capital_allocation_table_details(html) == (
        "Supply chain, technology and customer-facing initiatives $ 16,468",
        "Store and club remodels $ 5,571",
    )


def test_capital_table_details_preserve_units_and_period_headers() -> None:
    html = b"""<table>
      <tr><td>(Amounts in millions)</td></tr>
      <tr><td>Allocation of Capital Expenditures</td><td>2026</td><td>2025</td></tr>
      <tr><td>Supply chain and technology</td><td>16,468</td><td>14,603</td></tr>
      <tr><td>Total Capital Expenditures</td><td>26,642</td><td>23,783</td></tr>
    </table>"""

    details = extract_capital_allocation_table_details(html)

    assert details[0].startswith(
        "(Amounts in millions); Allocation of Capital Expenditures 2026 2025;"
    )
