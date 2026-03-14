# Generated migration for infrastructure fields

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('infrastructures', '0001_initial'),
        ('gouvernance', '0031_club_affiliation_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='infrastructure',
            name='etat_viabilite',
            field=models.CharField(
                blank=True,
                choices=[
                    ('OPERATIONNEL', 'Opérationnel'),
                    ('EN_TRAVAUX', 'En travaux'),
                    ('IMPRATICABLE', 'Impraticable'),
                ],
                default='OPERATIONNEL',
                help_text='État de viabilité de l\'infrastructure',
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='infrastructure',
            name='type_sol',
            field=models.CharField(
                blank=True,
                choices=[
                    ('SYNTHETIQUE', 'Synthétique'),
                    ('GAZON', 'Gazon'),
                    ('TERRE_BATTUE', 'Terre battue'),
                    ('BETON', 'Béton'),
                    ('AUTRE', 'Autre'),
                ],
                help_text='Type de sol de l\'infrastructure',
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='infrastructure',
            name='province_admin',
            field=models.ForeignKey(
                blank=True,
                help_text='Province administrative où se trouve l\'infrastructure',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='infrastructures',
                to='gouvernance.provadmin',
            ),
        ),
        migrations.AddField(
            model_name='infrastructure',
            name='interet_national',
            field=models.BooleanField(
                default=False,
                help_text='Infrastructure d\'intérêt national (modifiable uniquement par SG)',
            ),
        ),
    ]
