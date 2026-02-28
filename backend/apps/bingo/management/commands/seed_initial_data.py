import random

from django.core.management.base import BaseCommand

from apps.bingo.models import Cartela, Room


def generate_cartela() -> list[list[int | str]]:
    columns = [
        random.sample(range(1, 16), 5),   # B
        random.sample(range(16, 31), 5),  # I
        random.sample(range(31, 46), 5),  # N
        random.sample(range(46, 61), 5),  # G
        random.sample(range(61, 76), 5),  # O
    ]

    matrix: list[list[int | str]] = []
    for row_idx in range(5):
        row: list[int | str] = []
        for col_idx in range(5):
            row.append(columns[col_idx][row_idx])
        matrix.append(row)

    matrix[2][2] = "FREE"
    return matrix


class Command(BaseCommand):
    help = "Seed one active 10 birr room with 400 cartelas"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing cartelas and recreate all predefined cartelas for each room",
        )

    def handle(self, *args, **options):
        reset = bool(options.get("reset"))
        target_bet = 10
        target_total_cartelas = 400

        room = Room.objects.filter(bet_amount=target_bet).order_by("id").first()
        if not room:
            room = Room.objects.create(bet_amount=target_bet, total_cartelas=target_total_cartelas, is_active=True)

        Room.objects.exclude(id=room.id).update(is_active=False)

        room.total_cartelas = target_total_cartelas
        room.is_active = True
        room.save(update_fields=["total_cartelas", "is_active"])

        if reset:
            Cartela.objects.filter(room=room).delete()
        existing_cartelas = list(Cartela.objects.filter(room=room).order_by("id"))
        for cartela in existing_cartelas:
            cartela.numbers = generate_cartela()
            cartela.predefined = True
        if existing_cartelas:
            Cartela.objects.bulk_update(existing_cartelas, ["numbers", "predefined"])

        existing = len(existing_cartelas)
        to_create = room.total_cartelas - existing
        if to_create > 0:
            Cartela.objects.bulk_create(
                [Cartela(room=room, numbers=generate_cartela(), predefined=True) for _ in range(to_create)]
            )
        self.stdout.write(
            self.style.SUCCESS(
                f"Room #{room.id} ({target_bet} birr) seeded. Cartelas: {room.cartelas.count()}"
            )
        )
