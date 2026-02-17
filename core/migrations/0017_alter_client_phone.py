from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0016_traveler_flight_ticket_number"),
    ]

    operations = [
        migrations.AlterField(
            model_name="client",
            name="phone",
            field=models.CharField(max_length=13),
        ),
    ]
