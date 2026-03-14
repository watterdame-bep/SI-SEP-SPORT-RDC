# Generated migration for certificate fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gouvernance', '0022_add_statut_inspection'),
    ]

    operations = [
        migrations.AddField(
            model_name='institution',
            name='numero_homologation',
            field=models.CharField(
                blank=True,
                max_length=100,
                help_text="Numéro d'homologation du certificat (ex: RDC/MIN-SPORT/FED/2026-001)"
            ),
        ),
        migrations.AddField(
            model_name='institution',
            name='document_certificat_homologation',
            field=models.FileField(
                blank=True,
                null=True,
                upload_to='institutions/certificats/',
                max_length=500,
                help_text="Certificat d'Homologation Nationale (PDF)"
            ),
        ),
        migrations.AddField(
            model_name='institution',
            name='date_generation_certificat',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text="Date de génération du certificat"
            ),
        ),
    ]
