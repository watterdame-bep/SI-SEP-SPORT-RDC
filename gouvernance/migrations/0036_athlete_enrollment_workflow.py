# Generated migration for athlete enrollment workflow

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gouvernance', '0035_add_licence_fields'),
        ('core', '0008_add_infra_manager_role'),
    ]

    operations = [
        # Ajouter les champs d'enrôlement
        migrations.AddField(
            model_name='athlete',
            name='date_enrolement',
            field=models.DateTimeField(blank=True, help_text="Date d'enrôlement à la ligue provinciale", null=True),
        ),
        migrations.AddField(
            model_name='athlete',
            name='agent_enrolement',
            field=models.ForeignKey(blank=True, help_text="Agent de la ligue qui a effectué l'enrôlement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='athletes_enroles', to='core.profilutilisateur'),
        ),
        migrations.AddField(
            model_name='athlete',
            name='certificat_medical_enrolement',
            field=models.FileField(blank=True, help_text="Certificat médical vérifié lors de l'enrôlement", null=True, upload_to='athletes/certificats_enrolement/'),
        ),
        migrations.AddField(
            model_name='athlete',
            name='date_test_medical',
            field=models.DateField(blank=True, help_text='Date du test médical à la ligue', null=True),
        ),
        migrations.AddField(
            model_name='athlete',
            name='resultat_test_medical',
            field=models.CharField(blank=True, choices=[('APTE', 'Apte'), ('INAPTE', 'Inapte'), ('EN_ATTENTE', 'En attente')], default='EN_ATTENTE', help_text='Résultat du test médical', max_length=20),
        ),
        migrations.AddField(
            model_name='athlete',
            name='empreinte_digitale',
            field=models.FileField(blank=True, help_text='Fichier des empreintes digitales', null=True, upload_to='athletes/empreintes/'),
        ),
        migrations.AddField(
            model_name='athlete',
            name='observations_enrolement',
            field=models.TextField(blank=True, help_text="Observations lors de l'enrôlement"),
        ),
        # Ajouter le nouveau statut EN_ATTENTE_VALIDATION_LIGUE
        migrations.AlterField(
            model_name='athlete',
            name='statut_certification',
            field=models.CharField(
                choices=[
                    ('PROVISOIRE', 'Provisoire (En attente enrôlement Ligue)'),
                    ('EN_ATTENTE_VALIDATION_LIGUE', 'Enrôlé (En attente validation Ligue)'),
                    ('CERTIFIE_PROVINCIAL', 'Certifié Provincial (En attente validation Fédération)'),
                    ('CERTIFIE_NATIONAL', 'Certifié National (Homologué)'),
                    ('REJETE_LIGUE', 'Rejeté par la Ligue'),
                    ('REJETE_FEDERATION', 'Rejeté par la Fédération'),
                ],
                default='PROVISOIRE',
                help_text="Statut de certification de l'athlète dans le système",
                max_length=35
            ),
        ),
    ]
