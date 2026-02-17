from django.contrib.auth.hashers import make_password
from django.db import migrations


def create_default_admin_user(apps, schema_editor):
    CustomUser = apps.get_model("core", "CustomUser")

    user, _ = CustomUser.objects.get_or_create(
        email="admin@led.com",
        defaults={
            "role": "admin",
            "is_active": True,
            "is_admin": True,
            "password": make_password("ledadmin"),
        },
    )

    user.role = "admin"
    user.is_active = True
    user.is_admin = True
    user.password = make_password("ledadmin")
    user.save(update_fields=["role", "is_active", "is_admin", "password"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0018_bookedactivity_store_activity_name"),
    ]

    operations = [
        migrations.RunPython(create_default_admin_user, migrations.RunPython.noop),
    ]
