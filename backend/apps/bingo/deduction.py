from decimal import Decimal

DEDUCTION_TIERS = [
    (Decimal("40"), Decimal("10")),
    (Decimal("100"), Decimal("30")),
    (Decimal("160"), Decimal("50")),
    (Decimal("240"), Decimal("80")),
    (Decimal("300"), Decimal("100")),
    (Decimal("360"), Decimal("120")),
    (Decimal("450"), Decimal("150")),
    (Decimal("540"), Decimal("180")),
    (Decimal("600"), Decimal("200")),
    (Decimal("660"), Decimal("220")),
    (Decimal("900"), Decimal("300")),
    (Decimal("1200"), Decimal("400")),
    (Decimal("1500"), Decimal("500")),
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
