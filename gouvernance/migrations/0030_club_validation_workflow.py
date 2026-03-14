# Generated migration for club validation workflow

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gouvernance', '0029_add_club_document_fields'),
    ]

    operations = [
        # Add club validation status field to Institution
        migrations.AddField(
            model_name='institution',
            name='statut_validation_club',
            field=models.CharField(
                max_length=50,
                choices=[
                    ('', '—'),
                    ('EN_ATTENTE_VALIDATION', 'En attente de validation provinciale'),
                    ('VALIDEE_PROVINCIALE', 'Validée par la direction provinciale'),
                    ('REJETEE_PROVINCIALE', 'Rejetée par la direction provinciale'),
                    ('AFFILIEE', 'Affiliée (officielle)'),
                ],
                default='',
                blank=True,
                db_index=True,
                help_text='Statut de validation du club par la direction provinciale'
            ),
        ),
        
        # Add field to track if physical existence is confirmed
        migrations.AddField(
            model_name='institution',
            name='existence_physique_confirmee',
            field=models.BooleanField(
                default=False,
                help_text='Existence physique du club confirmée par la direction provinciale'
            ),
        ),
        
        # Create ClubValidation model
        migrations.CreateModel(
            name='ClubValidation',
            fields=[
                ('uid', models.UUIDField(default=None, editable=False, primary_key=True, serialize=False)),
                ('date_demande', models.DateTimeField(auto_now_add=True, help_text='Date de création de la demande')),
                ('date_validation', models.DateTimeField(null=True, blank=True, help_text='Date de validation par la direction provinciale')),
                ('existence_physique_confirmee', models.BooleanField(default=False, help_text='Existence physique confirmée')),
                ('motif_rejet', models.TextField(blank=True, help_text='Motif du rejet (si applicable)')),
                ('statut', models.CharField(
                    max_length=50,
                    choices=[
                        ('EN_ATTENTE', 'En attente'),
                        ('ACCEPTEE', 'Acceptée'),
                        ('REJETEE', 'Rejetée'),
                    ],
                    default='EN_ATTENTE',
                    db_index=True
                )),
                ('club', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='validation_club', to='gouvernance.institution')),
                ('division_provinciale', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='validations_clubs', to='gouvernance.institution', help_text='Direction provinciale responsable de la validation')),
                ('validee_par', models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name='clubs_valides', to='core.profilutilisateur', help_text='Utilisateur qui a validé')),
            ],
            options={
                'db_table': 'club_validation',
                'verbose_name': 'Validation de club',
                'verbose_name_plural': 'Validations de clubs',
            },
        ),
    ]
