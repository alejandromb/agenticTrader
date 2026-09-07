"""Deterministic, coverage-aware equity context. No investment recommendations."""

from decimal import Decimal, localcontext

from agentic_trading.portfolio_snapshots import PortfolioObservation


def equity_context(observation: PortfolioObservation) -> dict:
    """Return decimal strings and explicit denominators, never infer missing values."""
    observation = PortfolioObservation.model_validate_json(
        observation.model_dump_json()
    )
    holdings = observation.holdings
    unsupported = any(h.position_type not in ("long", "empty") for h in holdings)
    # Keep all input digits for multiplication/subtraction; ratios have ample precision.
    numbers = [
        v
        for h in holdings
        for v in (h.quantity, h.quote, h.average_cost)
        if v is not None
    ]
    if observation.account_value is not None:
        numbers.append(observation.account_value)
    with localcontext() as ctx:
        ctx.prec = max(
            50,
            sum(len(v.as_tuple().digits) + abs(v.as_tuple().exponent) for v in numbers)
            + 10,
        )
        values = {
            h.symbol: h.quantity * h.quote if h.quote is not None else None
            for h in holdings
        }
        complete = observation.coverage == "complete" and not unsupported
        total = sum((v for v in values.values() if v is not None), Decimal(0))
        denominator = total if complete and total > 0 else None
        reasons = list(observation.limitations)
        if denominator is None:
            reasons.append(
                "Equity weights unavailable: incomplete or unsupported "
                "holdings, or nonpositive priced equity total."
            )
        rows = []
        for h in holdings:
            value = values[h.symbol]
            supported = h.position_type in ("long", "empty")
            pnl = (
                h.quantity * (h.quote - h.average_cost)
                if supported and h.quote is not None and h.average_cost is not None
                else None
            )
            account = observation.account_value
            rows.append(
                {
                    "symbol": h.symbol,
                    "position_value": str(value) if value is not None else None,
                    "estimated_unrealized_result": str(pnl)
                    if pnl is not None
                    else None,
                    "equity_weight": str(value / denominator)
                    if value is not None and denominator is not None
                    else None,
                    "account_weight": str(value / account)
                    if supported
                    and value is not None
                    and account is not None
                    and account > 0
                    else None,
                }
            )
        return {
            "formula_version": "1.0",
            "equity_weight_denominator": str(denominator) if denominator else None,
            "broker_account_value": (
                str(observation.account_value)
                if observation.account_value is not None
                else None
            ),
            "holdings": rows,
            "limitations": reasons,
        }
