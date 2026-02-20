# Generated manually for SI-SEP Sport RDC - Module Infrastructures

import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('gouvernance', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TypeInfrastructure',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('designation', models.CharField(max_length=100)),
                ('code', models.CharField(blank=True, max_length=20, unique=True)),
            ],
            options={
                'db_table': 'type_infrastructure',
                'verbose_name': "Type d'infrastructure",
                'verbose_name_plural': "Types d'infrastructure",
            },
        ),
        migrations.CreateModel(
            name='Infrastructure',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('code_homologation', models.CharField(max_length=50, unique=True)),
                ('nom', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, help_text='Latitude (ex: -4.321000)', max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, help_text='Longitude (ex: 15.312500)', max_digits=9, null=True)),
                ('adresse_texte', models.CharField(blank=True, max_length=500)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('actif', models.BooleanField(default=True)),
                ('gestionnaire', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='infrastructures_gerees', to='gouvernance.institution')),
                ('territoire', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='infrastructures', to='gouvernance.territoireville')),
                ('type_infrastructure', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='infrastructures', to='infrastructures.typeinfrastructure')),
            ],
            options={
                'db_table': 'infrastructure',
                'verbose_name': 'Infrastructure sportive',
                'verbose_name_plural': 'Infrastructures sportives',
                'ordering': ['nom'],
            },
        ),
        migrations.CreateModel(
            name='SuiviTechnique',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date_controle', models.DateField()),
                ('etat_general', models.CharField(blank=True, max_length=50)),
                ('capacite_spectateurs', models.PositiveIntegerField(blank=True, null=True)),
                ('observations', models.TextField(blank=True)),
                ('rapport_url', models.URLField(blank=True, max_length=500)),
                ('infrastructure', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='suivis_techniques', to='infrastructures.infrastructure')),
            ],
            options={
                'db_table': 'suivi_technique',
                'verbose_name': 'Suivi technique',
                'verbose_name_plural': 'Suivis techniques',
                'ordering': ['-date_controle'],
            },
        ),
        migrations.CreateModel(
            name='RevenuInfrastructure',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date_debut', models.DateField()),
                ('date_fin', models.DateField(blank=True, null=True)),
                ('type_revenu', models.CharField(blank=True, max_length=100)),
                ('montant', models.DecimalField(decimal_places=2, max_digits=14)),
                ('devise', models.CharField(default='CDF', max_length=3)),
                ('libelle', models.CharField(blank=True, max_length=255)),
                ('infrastructure', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='revenus', to='infrastructures.infrastructure')),
            ],
            options={
                'db_table': 'revenu_infrastructure',
                'verbose_name': 'Revenu infrastructure',
                'verbose_name_plural': 'Revenus infrastructures',
                'ordering': ['-date_debut'],
            },
        ),
    ]
