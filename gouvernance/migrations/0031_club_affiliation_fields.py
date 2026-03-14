# Generated migration for club affiliation fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gouvernance', '0030_club_validation_workflow'),
    ]

    operations = [
        migrations.AddField(
            model_name='institution',
            name='numero_affiliation',
            field=models.CharField(blank=True, help_text="Numéro d'affiliation unique (ex: A-2026-FÉDÉ-PROV-001)", max_length=100),
        ),
        migrations.AddField(
            model_name='institution',
            name='date_affiliation',
            field=models.DateTimeField(blank=True, help_text='Date et heure de l\'affiliation officielle', null=True),
        ),
        migrations.AddField(
            model_name='institution',
            name='document_acte_affiliation',
            field=models.FileField(blank=True, help_text='Acte d\'Affiliation Provincial (PDF)', max_length=500, null=True, upload_to='institutions/actes_affiliation/'),
        ),
    ]
