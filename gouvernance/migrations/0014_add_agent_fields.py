# Generated migration for creating Agent table

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('gouvernance', '0013_add_arrete_vu_par_sg'),
    ]

    operations = [
        migrations.CreateModel(
            name='Agent',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('matricule', models.CharField(
                    blank=True,
                    help_text='Matricule unique de l\'agent (ex: MIN-2026-001)',
                    max_length=50,
                    null=True,
                    unique=True,
                )),
                ('signature_image', models.ImageField(
                    blank=True,
                    help_text='Signature scannée de l\'agent',
                    null=True,
                    upload_to='agents/signatures/',
                )),
                ('sceau_image', models.ImageField(
                    blank=True,
                    help_text='Sceau officiel (si applicable)',
                    null=True,
                    upload_to='agents/sceaux/',
                )),
                ('date_enregistrement', models.DateTimeField(auto_now_add=True)),
                ('institution', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='agents',
                    to='gouvernance.institution',
                )),
                ('personne', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='agent',
                    to='gouvernance.personne',
                )),
            ],
            options={
                'db_table': 'agent',
                'verbose_name': 'Agent',
                'verbose_name_plural': 'Agents',
            },
        ),
    ]
