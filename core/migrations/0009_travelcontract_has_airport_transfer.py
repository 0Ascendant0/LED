from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_alter_travelcontract_total_package_price"),
    ]

    operations = [
        migrations.AddField(
            model_name="travelcontract",
            name="has_airport_transfer",
            field=models.BooleanField(default=False),
        ),
    ]

