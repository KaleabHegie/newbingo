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
