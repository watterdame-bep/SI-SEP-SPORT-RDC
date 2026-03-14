# Generated migration for athlete certification workflow

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gouvernance', '0033_athlete_model'),
        ('core', '0008_add_infra_manager_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='athlete',
            name='statut_certification',
            field=models.CharField(
                choices=[
                    ('PROVISOIRE', 'Provisoire (En attente validation Ligue)'),
                    ('CERTIFIE_PROVINCIAL', 'Certifié Provincial (En attente validation Fédération)'),
                    ('CERTIFIE_NATIONAL', 'Certifié National (Homologué)'),
                    ('REJETE_LIGUE', 'Rejeté par la Ligue'),
                    ('REJETE_FEDERATION', 'Rejeté par la Fédération'),
                ],
                default='PROVISOIRE',
                help_text="Statut de certification de l'athlète dans le système",
                max_length=30
            ),
        ),
        migrations.AddField(
            model_name='athlete',
            name='date_validation_ligue',
            field=models.DateTimeField(
                blank=True,
                help_text='Date de validation par la Ligue Provinciale',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='athlete',
            name='date_validation_federation',
            field=models.DateTimeField(
                blank=True,
                help_text='Date de validation par la Fédération Nationale',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='athlete',
            name='validateur_ligue',
            field=models.ForeignKey(
                blank=True,
                help_text='Secrétaire de la Ligue qui a validé',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='athletes_valides_ligue',
                to='core.profilutilisateur'
            ),
        ),
        migrations.AddField(
            model_name='athlete',
            name='validateur_federation',
            field=models.ForeignKey(
                blank=True,
                help_text='Secrétaire de la Fédération qui a validé',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='athletes_valides_federation',
                to='core.profilutilisateur'
            ),
        ),
        migrations.AddField(
            model_name='athlete',
            name='motif_rejet_ligue',
            field=models.TextField(
                blank=True,
                help_text='Motif de rejet par la Ligue'
            ),
        ),
        migrations.AddField(
            model_name='athlete',
            name='motif_rejet_federation',
            field=models.TextField(
                blank=True,
                help_text='Motif de rejet par la Fédération'
            ),
        ),
    ]
