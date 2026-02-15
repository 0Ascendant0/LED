from decimal import Decimal

from django.db import migrations, models


def sync_totals_with_transfer_price(apps, schema_editor):
    TravelContract = apps.get_model("core", "TravelContract")
    for contract in TravelContract.objects.all():
        if not contract.has_airport_transfer:
            contract.airport_transfer_price = Decimal("0.00")
            contract.save(update_fields=["airport_transfer_price"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_travelcontract_has_airport_transfer"),
    ]

    operations = [
        migrations.AddField(
            model_name="travelcontract",
            name="airport_transfer_price",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12),
        ),
        migrations.RunPython(sync_totals_with_transfer_price, migrations.RunPython.noop),
    ]

