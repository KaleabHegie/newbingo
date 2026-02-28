from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bingo", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="game",
            name="countdown_started_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
