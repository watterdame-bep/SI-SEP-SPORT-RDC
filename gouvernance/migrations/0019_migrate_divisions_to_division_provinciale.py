# Data migration to move divisions from institution table to division_provinciale table

from django.db import migrations


def migrate_divisions(apps, schema_editor):
    """Migrate provincial divisions from Institution to DivisionProvinciale."""
    Institution = apps.get_model('gouvernance', 'Institution')
    DivisionProvinciale = apps.get_model('gouvernance', 'DivisionProvinciale')
    AdresseContact = apps.get_model('gouvernance', 'AdresseContact')
    ProvAdmin = apps.get_model('gouvernance', 'ProvAdmin')
    
    # Get all provincial divisions from Institution table
    divisions = Institution.objects.filter(
        niveau_territorial='PROVINCIAL'
    ).select_related('province_admin')
    
    for division in divisions:
        # Check if this division already exists in DivisionProvinciale
        if not DivisionProvinciale.objects.filter(province=division.province_admin).exists():
            # Get address if it exists
            adresse = AdresseContact.objects.filter(institution=division).first()
            
            # Create new DivisionProvinciale record
            DivisionProvinciale.objects.create(
                province=division.province_admin,
                code=division.code,
                nom_officiel=division.nom_officiel,
                adresse=adresse.avenue if adresse else '',
                telephone=adresse.telephone if adresse else '',
                email=adresse.email if adresse else '',
                statut='ACTIVE' if division.statut_activation == 'ACTIVE' else 'INACTIVE',
                chef=None,  # Will be assigned separately
            )


def reverse_migrate(apps, schema_editor):
    """Reverse migration - delete DivisionProvinciale records."""
    DivisionProvinciale = apps.get_model('gouvernance', 'DivisionProvinciale')
    DivisionProvinciale.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('gouvernance', '0018_chef_division'),
    ]

    operations = [
        migrations.RunPython(migrate_divisions, reverse_migrate),
    ]
