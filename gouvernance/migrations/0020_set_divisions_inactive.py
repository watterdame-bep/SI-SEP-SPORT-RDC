# Migration to set all existing divisions to INACTIVE status

from django.db import migrations


def set_divisions_inactive(apps, schema_editor):
    """Set all existing divisions to INACTIVE status."""
    DivisionProvinciale = apps.get_model('gouvernance', 'DivisionProvinciale')
    DivisionProvinciale.objects.all().update(statut='INACTIVE')


def reverse_set_divisions_inactive(apps, schema_editor):
    """Reverse: set divisions back to ACTIVE."""
    DivisionProvinciale = apps.get_model('gouvernance', 'DivisionProvinciale')
    DivisionProvinciale.objects.all().update(statut='ACTIVE')


class Migration(migrations.Migration):

    dependencies = [
        ('gouvernance', '0019_migrate_divisions_to_division_provinciale'),
    ]

    operations = [
        migrations.RunPython(set_divisions_inactive, reverse_set_divisions_inactive),
    ]
