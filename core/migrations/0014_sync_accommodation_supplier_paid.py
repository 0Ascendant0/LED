from django.db import migrations


def sync_accommodation_supplier_paid(apps, schema_editor):
    AccommodationBooking = apps.get_model("core", "AccommodationBooking")
    for booking in AccommodationBooking.objects.all():
        has_confirmation = bool((booking.confirmation_number or "").strip())
        expected_status = "confirmed" if has_confirmation else "not_confirmed"
        expected_paid = has_confirmation
        updates = {}
        if booking.status != expected_status:
            updates["status"] = expected_status
        if booking.is_supplier_paid != expected_paid:
            updates["is_supplier_paid"] = expected_paid
        if updates:
            AccommodationBooking.objects.filter(pk=booking.pk).update(**updates)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0013_remove_airporttransfer_dropoff_location_and_more"),
    ]

    operations = [
        migrations.RunPython(sync_accommodation_supplier_paid, migrations.RunPython.noop),
    ]
