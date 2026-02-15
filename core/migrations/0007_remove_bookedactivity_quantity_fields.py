from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_travelcontract_has_flight_included_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="bookedactivity",
            name="quantity_adult",
        ),
        migrations.RemoveField(
            model_name="bookedactivity",
            name="quantity_child",
        ),
        migrations.RemoveField(
            model_name="bookedactivity",
            name="quantity_infant",
        ),
    ]

