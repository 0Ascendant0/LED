from django.db import migrations, models
import django.db.models.deletion


def backfill_activity_names(apps, schema_editor):
    BookedActivity = apps.get_model("core", "BookedActivity")
    for booking in BookedActivity.objects.select_related("activity").all():
        if getattr(booking, "activity_name", "").strip():
            continue
        name = ""
        if booking.activity_id and booking.activity:
            name = (booking.activity.name or "").strip()
        if not name:
            name = "Unnamed Activity"
        booking.activity_name = name
        booking.save(update_fields=["activity_name"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0017_alter_client_phone"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bookedactivity",
            name="activity",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="core.activitytemplate",
            ),
        ),
        migrations.AddField(
            model_name="bookedactivity",
            name="activity_name",
            field=models.CharField(default="", max_length=200),
            preserve_default=False,
        ),
        migrations.RunPython(backfill_activity_names, migrations.RunPython.noop),
    ]
