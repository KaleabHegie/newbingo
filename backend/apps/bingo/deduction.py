from decimal import Decimal

DEDUCTION_TIERS = [
    (Decimal("50"), Decimal("10")),
    (Decimal("100"), Decimal("15")),
    (Decimal("150"), Decimal("20")),
    (Decimal("200"), Decimal("25")),
    (Decimal("300"), Decimal("35")),
    (Decimal("400"), Decimal("50")),
    (Decimal("500"), Decimal("65")),
    (Decimal("600"), Decimal("80")),
    (Decimal("700"), Decimal("95")),
    (Decimal("800"), Decimal("110")),
    (Decimal("900"), Decimal("130")),
    (Decimal("1000"), Decimal("150")),
    (Decimal("1100"), Decimal("170")),
    (Decimal("1200"), Decimal("190")),
    (Decimal("1300"), Decimal("210")),
    (Decimal("1400"), Decimal("240")),
    (Decimal("1500"), Decimal("270")),
    (Decimal("1600"), Decimal("300")),
    (Decimal("1700"), Decimal("330")),
    (Decimal("1800"), Decimal("360")),
    (Decimal("1900"), Decimal("380")),
    (Decimal("2000"), Decimal("400")),
    (Decimal("2100"), Decimal("420")),
    (Decimal("2200"), Decimal("440")),
    (Decimal("2300"), Decimal("460")),
    (Decimal("2400"), Decimal("480")),
    (Decimal("2500"), Decimal("500")),
    (Decimal("2600"), Decimal("520")),
    (Decimal("2700"), Decimal("540")),
    (Decimal("2800"), Decimal("560")),
    (Decimal("2900"), Decimal("580")),
    (Decimal("3000"), Decimal("600")),
    (Decimal("3100"), Decimal("620")),
    (Decimal("3200"), Decimal("640")),
    (Decimal("3300"), Decimal("660")),
    (Decimal("3400"), Decimal("680")),
    (Decimal("3500"), Decimal("700")),
    (Decimal("3600"), Decimal("720")),
    (Decimal("3700"), Decimal("740")),
    (Decimal("3800"), Decimal("760")),
    (Decimal("3900"), Decimal("780")),
    (Decimal("4000"), Decimal("800")),
    (Decimal("4100"), Decimal("820")),
    (Decimal("4200"), Decimal("840")),
    (Decimal("4300"), Decimal("860")),
    (Decimal("4400"), Decimal("880")),
    (Decimal("4500"), Decimal("900")),
    (Decimal("4600"), Decimal("920")),
    (Decimal("4700"), Decimal("940")),
    (Decimal("4800"), Decimal("960")),
    (Decimal("4900"), Decimal("980")),
    (Decimal("5000"), Decimal("1000")),
]


def calculate_deduction(total_pool: Decimal) -> Decimal:
    deduction = Decimal("0")
    for min_pool, tier in DEDUCTION_TIERS:
        if total_pool >= min_pool:
            deduction = tier
        else:
            break
    return deduction


def calculate_prize(total_players: int, bet_amount: Decimal) -> tuple[Decimal, Decimal]:
    pool = Decimal(total_players) * bet_amount
    deduction = calculate_deduction(pool)
    return max(pool - deduction, Decimal("0")), deduction
