# Generated manually for SI-SEP Sport RDC - Module Gouvernance

import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ProvAdmin',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('designation', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('code', models.CharField(blank=True, max_length=50, unique=True)),
            ],
            options={
                'db_table': 'prov_admin',
                'verbose_name': 'Division Provinciale',
                'verbose_name_plural': 'Divisions Provinciales',
            },
        ),
        migrations.CreateModel(
            name='TerritoireVille',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('designation', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('code', models.CharField(blank=True, max_length=50, unique=True)),
                ('province_admin', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='territoires_villes', to='gouvernance.provadmin')),
            ],
            options={
                'db_table': 'territoire_ville',
                'verbose_name': 'Territoire / Ville',
                'verbose_name_plural': 'Territoires / Villes',
            },
        ),
        migrations.CreateModel(
            name='EtatAgrement',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('designation', models.CharField(max_length=100)),
                ('code', models.CharField(blank=True, max_length=20, unique=True)),
            ],
            options={
                'db_table': 'etat_agrement',
                'verbose_name': "État d'agrément",
                'verbose_name_plural': "États d'agrément",
            },
        ),
        migrations.CreateModel(
            name='EtatAdministrative',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('num_agrement_admin', models.CharField(max_length=100, unique=True)),
                ('date_delivrance', models.DateField(blank=True, null=True)),
                ('est_affiliee', models.CharField(blank=True, max_length=255)),
                ('docum_agrement_url', models.URLField(blank=True, max_length=500)),
                ('validation_admin', models.CharField(blank=True, max_length=50)),
                ('valid_tec_sportive', models.CharField(blank=True, max_length=50)),
                ('etat_agrement', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='etats_administratifs', to='gouvernance.etatagrement')),
            ],
            options={
                'db_table': 'etat_administrative',
                'verbose_name': 'Agrément administratif',
                'verbose_name_plural': 'Agréments administratifs',
            },
        ),
        migrations.CreateModel(
            name='TypeInstitution',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('designation', models.CharField(max_length=255)),
                ('code', models.CharField(blank=True, max_length=50, unique=True)),
            ],
            options={
                'db_table': 'type_institution',
                'verbose_name': "Type d'institution",
                'verbose_name_plural': "Types d'institution",
            },
        ),
        migrations.CreateModel(
            name='SecteurCommune',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('designation', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('territoire', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='secteurs_communes', to='gouvernance.territoireville')),
            ],
            options={
                'db_table': 'secteur_commune',
                'verbose_name': 'Secteur / Commune',
                'verbose_name_plural': 'Secteurs / Communes',
            },
        ),
        migrations.CreateModel(
            name='GroupementQuartier',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('designation', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('secteur', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='groupements_quartiers', to='gouvernance.secteurcommune')),
            ],
            options={
                'db_table': 'groupement_quartier',
                'verbose_name': 'Groupement / Quartier',
                'verbose_name_plural': 'Groupements / Quartiers',
            },
        ),
        migrations.CreateModel(
            name='VillageQuartier',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('designation', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('groupement', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='villages_quartiers', to='gouvernance.groupementquartier')),
            ],
            options={
                'db_table': 'village_quartier',
                'verbose_name': 'Village / Quartier',
                'verbose_name_plural': 'Villages / Quartiers',
            },
        ),
        migrations.CreateModel(
            name='Institution',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('code', models.CharField(max_length=50, unique=True)),
                ('nom_officiel', models.CharField(max_length=255)),
                ('sigle', models.CharField(blank=True, max_length=50)),
                ('statut_juridique', models.CharField(blank=True, max_length=100)),
                ('date_creation', models.DateField(blank=True, null=True)),
                ('nombre_pers_admin', models.PositiveIntegerField(default=0)),
                ('nombre_pers_tech', models.PositiveIntegerField(default=0)),
                ('partenaire', models.CharField(blank=True, max_length=255)),
                ('email_officiel', models.EmailField(blank=True, max_length=254)),
                ('telephone_off', models.CharField(blank=True, max_length=50)),
                ('etat_administrative', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='institution', to='gouvernance.etatadministrative')),
                ('institution_tutelle', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='institutions_fille', to='gouvernance.institution')),
                ('type_institution', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='institutions', to='gouvernance.typeinstitution')),
            ],
            options={
                'db_table': 'institution',
                'verbose_name': 'Institution',
                'verbose_name_plural': 'Institutions',
                'ordering': ['nom_officiel'],
            },
        ),
        migrations.CreateModel(
            name='AdresseContact',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('avenue', models.CharField(blank=True, max_length=255)),
                ('numero', models.PositiveIntegerField(blank=True, null=True)),
                ('gps', models.CharField(blank=True, help_text='Coordonnées GPS (lat, lon)', max_length=100)),
                ('telephone', models.CharField(blank=True, max_length=50)),
                ('institution', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='adresses_contact', to='gouvernance.institution')),
                ('quartier_village', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='adresses', to='gouvernance.villagequartier')),
            ],
            options={
                'db_table': 'adresse_contact',
                'verbose_name': 'Adresse de contact',
                'verbose_name_plural': 'Adresses de contact',
            },
        ),
        migrations.CreateModel(
            name='Personne',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('nom', models.CharField(max_length=100)),
                ('postnom', models.CharField(blank=True, max_length=100)),
                ('prenom', models.CharField(blank=True, max_length=100)),
                ('sexe', models.CharField(blank=True, choices=[('M', 'Masculin'), ('F', 'Féminin')], max_length=1)),
                ('date_naissance', models.DateField(blank=True, null=True)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('photo', models.URLField(blank=True, max_length=500)),
                ('adresse', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='personnes', to='gouvernance.adressecontact')),
                ('lieu_naissance', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='personnes_nees', to='gouvernance.territoireville')),
            ],
            options={
                'db_table': 'personne',
                'verbose_name': 'Personne',
                'verbose_name_plural': 'Personnes',
                'ordering': ['nom', 'postnom', 'prenom'],
            },
        ),
        migrations.CreateModel(
            name='Fonction',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('designation', models.CharField(max_length=150)),
                ('ordre_priorite', models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                'db_table': 'fonction',
                'verbose_name': 'Fonction',
                'verbose_name_plural': 'Fonctions',
                'ordering': ['ordre_priorite', 'designation'],
            },
        ),
        migrations.CreateModel(
            name='Membre',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('institution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='membres', to='gouvernance.institution')),
                ('fonction', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='membres', to='gouvernance.fonction')),
                ('personne', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='membres', to='gouvernance.personne')),
            ],
            options={
                'db_table': 'membre',
                'verbose_name': 'Membre',
                'verbose_name_plural': 'Membres',
                'unique_together': {('personne', 'institution', 'fonction')},
            },
        ),
        migrations.CreateModel(
            name='Mandat',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date_debut', models.DateField()),
                ('date_fin', models.DateField(blank=True, null=True)),
                ('statut_mandat', models.CharField(blank=True, max_length=50)),
                ('docum_nomination_url', models.URLField(blank=True, max_length=500)),
                ('fonction', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='mandats', to='gouvernance.fonction')),
                ('institution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mandats', to='gouvernance.institution')),
                ('membre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mandats', to='gouvernance.membre')),
            ],
            options={
                'db_table': 'mandat',
                'verbose_name': 'Mandat',
                'verbose_name_plural': 'Mandats',
                'ordering': ['-date_debut'],
            },
        ),
    ]
