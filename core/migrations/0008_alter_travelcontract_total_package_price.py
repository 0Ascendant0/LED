from decimal import Decimal

from django.db import migrations, models
from django.db.models import Sum
from django.db.models.functions import Coalesce


def recalculate_contract_totals(apps, schema_editor):
    TravelContract = apps.get_model("core", "TravelContract")
    Traveler = apps.get_model("core", "Traveler")

    totals = (
        Traveler.objects.values("contract_id")
        .annotate(total=Coalesce(Sum("price"), Decimal("0.00")))
    )
    totals_map = {row["contract_id"]: row["total"] for row in totals}

    for contract in TravelContract.objects.all():
        contract.total_package_price = totals_map.get(contract.id, Decimal("0.00"))
        contract.save(update_fields=["total_package_price"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0007_remove_bookedactivity_quantity_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="travelcontract",
            name="total_package_price",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12),
        ),
        migrations.RunPython(recalculate_contract_totals, migrations.RunPython.noop),
    ]

