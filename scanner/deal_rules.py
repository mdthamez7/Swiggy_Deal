def evaluate(current, mrp, history, min_history, previous_low_drop,
             stable_mrp_drop, mrp_tolerance):
    prior_prices = [p for p, _ in history if p is not None]
    prior_mrps = [m for _, m in history if m is not None and m > 0]

    previous_low = min(prior_prices) if prior_prices else None
    typical = (
        sum(prior_prices) / len(prior_prices)
        if prior_prices else None
    )

    reasons = []

    discount = None
    if mrp and mrp > 0 and current <= mrp:
        discount = (mrp - current) / mrp
        if discount >= 0.90:
            reasons.append("90%+ below MRP")
        elif discount >= 0.80:
            reasons.append("80%+ below MRP")
        elif discount >= 0.50:
            reasons.append("50%+ below MRP")
        elif discount >= 0.20:
            reasons.append("20%+ below MRP")

    if (
        len(prior_prices) >= min_history
        and previous_low is not None
        and current <= previous_low * (1 - previous_low_drop)
    ):
        reasons.append("20%+ below previous low")

    stable_mrp = False
    if prior_mrps and mrp:
        avg_mrp = sum(prior_mrps) / len(prior_mrps)
        stable_mrp = (
            abs(mrp - avg_mrp) / avg_mrp <= mrp_tolerance
        )

    if (
        stable_mrp
        and typical is not None
        and current <= typical * (1 - stable_mrp_drop)
    ):
        reasons.append("stable-MRP historical-price drop")

    return {
        "is_deal": bool(reasons),
        "reasons": reasons,
        "previous_low": previous_low,
        "typical": typical,
        "discount": discount,
    }
