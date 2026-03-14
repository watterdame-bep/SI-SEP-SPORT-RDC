# Generated migration for adding licence fields to Athlete model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gouvernance', '0034_athlete_certification_workflow'),
    ]

    operations = [
        migrations.AddField(
            model_name='athlete',
            name='numero_licence',
            field=models.CharField(blank=True, help_text="Numéro de licence sportive (identique au numéro sportif)", max_length=50),
        ),
        migrations.AddField(
            model_name='athlete',
            name='date_emission_licence',
            field=models.DateField(blank=True, help_text="Date d'émission de la licence", null=True),
        ),
        migrations.AddField(
            model_name='athlete',
            name='date_expiration_licence',
            field=models.DateField(blank=True, help_text="Date d'expiration de la licence (1 an après émission)", null=True),
        ),
        migrations.AddField(
            model_name='athlete',
            name='licence_pdf',
            field=models.FileField(blank=True, help_text='Fichier PDF de la licence sportive', null=True, upload_to='licences/'),
        ),
    ]
