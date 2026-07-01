from agentic_trading.filing_sections import extract_business_and_risk_evidence


def test_extracts_bounded_item_one_and_risk_evidence() -> None:
    html = b"""<html>
      <div>ITEM 1.</div><div>BUSINESS</div>
      <p>We operate three business segments serving customers through stores
         and ecommerce services.</p>
      <div>ITEM 1A.</div><div>RISK FACTORS</div>
      <p>Competition and supply chain disruption could adversely affect our
         operations and results.</p>
      <div>ITEM 1B.</div><div>UNRESOLVED STAFF COMMENTS</div>
    </html>"""

    evidence = extract_business_and_risk_evidence(html)

    assert evidence.business == (
        "We operate three business segments serving customers through stores "
        "and ecommerce services.",
    )
    assert evidence.risks == (
        "Competition and supply chain disruption could adversely affect our "
        "operations and results.",
    )


def test_missing_sections_are_explicitly_empty() -> None:
    evidence = extract_business_and_risk_evidence(b"<html>No filing sections</html>")

    assert evidence.business == ()
    assert evidence.risks == ()
