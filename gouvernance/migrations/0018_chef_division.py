# Generated migration for DivisionProvinciale model

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('gouvernance', '0017_add_commune_to_adresse_contact'),
    ]

    operations = [
        migrations.CreateModel(
            name='DivisionProvinciale',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('code', models.CharField(help_text='Code unique de la division (ex: DIV-KINSHASA)', max_length=50, unique=True)),
                ('nom_officiel', models.CharField(help_text='Nom officiel de la division', max_length=255)),
                ('adresse', models.CharField(blank=True, help_text='Adresse physique de la division', max_length=500)),
                ('telephone', models.CharField(blank=True, help_text='Numéro de téléphone', max_length=50)),
                ('email', models.EmailField(blank=True, help_text='Email de la division', max_length=254)),
                ('statut', models.CharField(choices=[('ACTIVE', 'Active'), ('INACTIVE', 'Inactive'), ('SUSPENDUE', 'Suspendue')], default='ACTIVE', help_text='Statut de la division', max_length=20)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('chef', models.ForeignKey(blank=True, help_text='Agent assigné comme Chef de Division', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='divisions_chef', to='gouvernance.agent')),
                ('province', models.OneToOneField(help_text='Province administrative', on_delete=django.db.models.deletion.CASCADE, related_name='division_provinciale', to='gouvernance.provadmin')),
            ],
            options={
                'verbose_name': 'Division Provinciale',
                'verbose_name_plural': 'Divisions Provinciales',
                'db_table': 'division_provinciale',
                'ordering': ['province__designation'],
            },
        ),
    ]
