# Generated migration for adding detailed inspection criteria fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gouvernance', '0026_validationligue_date_transfert_division_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='validationligue',
            name='conformite_mandat',
            field=models.BooleanField(blank=True, help_text='Conformité du Mandat : Les délégués provinciaux sont-ils reconnus par la Fédération Nationale ?', null=True),
        ),
        migrations.AddField(
            model_name='validationligue',
            name='siege_social_provincial',
            field=models.BooleanField(blank=True, help_text='Siège Social Provincial : L\'adresse physique dans la province est-elle vérifiée et fonctionnelle ?', null=True),
        ),
        migrations.AddField(
            model_name='validationligue',
            name='existence_clubs',
            field=models.BooleanField(blank=True, help_text='Existence des Clubs : La ligue dispose-t-elle du nombre minimum de clubs actifs requis ?', null=True),
        ),
        migrations.AddField(
            model_name='validationligue',
            name='rapport_inspection',
            field=models.FileField(blank=True, help_text='Rapport d\'inspection provinciale signé', max_length=500, null=True, upload_to='institutions/rapports_inspection/'),
        ),
    ]
