from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bingo", "0003_game_countdown_started_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="room",
            name="bet_amount",
            field=models.PositiveIntegerField(),
        ),
    ]
