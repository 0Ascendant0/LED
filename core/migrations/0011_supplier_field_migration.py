from django.db import migrations, models


def backfill_supplier_names(apps, schema_editor):
    ActivityTemplate = apps.get_model("core", "ActivityTemplate")
    BookedActivity = apps.get_model("core", "BookedActivity")
    AccommodationBooking = apps.get_model("core", "AccommodationBooking")
    FlightBooking = apps.get_model("core", "FlightBooking")
    AirportTransfer = apps.get_model("core", "AirportTransfer")

    for activity in ActivityTemplate.objects.select_related("supplier").all():
        if not activity.supplier_name and activity.supplier_id:
            activity.supplier_name = activity.supplier.name or ""
            activity.save(update_fields=["supplier_name"])

    for booking in BookedActivity.objects.select_related("activity", "activity__supplier").all():
        if booking.supplier_name:
            continue
        if booking.activity and booking.activity.supplier_name:
            booking.supplier_name = booking.activity.supplier_name
        elif booking.activity and booking.activity.supplier_id:
            booking.supplier_name = booking.activity.supplier.name or ""
        else:
            booking.supplier_name = ""
        booking.save(update_fields=["supplier_name"])

    for booking in AccommodationBooking.objects.select_related("supplier").all():
        if not booking.supplier_name and booking.supplier_id:
            booking.supplier_name = booking.supplier.name or ""
            booking.save(update_fields=["supplier_name"])

    for booking in FlightBooking.objects.select_related("supplier").all():
        if not booking.supplier_name and booking.supplier_id:
            booking.supplier_name = booking.supplier.name or ""
            booking.save(update_fields=["supplier_name"])

    for booking in AirportTransfer.objects.select_related("supplier").all():
        if not booking.supplier_name and booking.supplier_id:
            booking.supplier_name = booking.supplier.name or ""
            booking.save(update_fields=["supplier_name"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_travelcontract_airport_transfer_price"),
    ]

    operations = [
        migrations.AddField(
            model_name="activitytemplate",
            name="supplier_name",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="bookedactivity",
            name="is_supplier_paid",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="bookedactivity",
            name="supplier_name",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="accommodationbooking",
            name="is_supplier_paid",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="accommodationbooking",
            name="supplier_name",
            field=models.CharField(default="", max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="flightbooking",
            name="is_supplier_paid",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="flightbooking",
            name="supplier_name",
            field=models.CharField(default="", max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="airporttransfer",
            name="is_supplier_paid",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="airporttransfer",
            name="supplier_name",
            field=models.CharField(default="", max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="travelcontract",
            name="is_travel_insurance_paid",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(backfill_supplier_names, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="activitytemplate",
            name="supplier",
        ),
        migrations.RemoveField(
            model_name="accommodationbooking",
            name="supplier",
        ),
        migrations.RemoveField(
            model_name="flightbooking",
            name="supplier",
        ),
        migrations.RemoveField(
            model_name="airporttransfer",
            name="supplier",
        ),
    ]
