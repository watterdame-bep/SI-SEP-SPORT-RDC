# Migration: champ province_admin pour DIRECTEUR_PROVINCIAL

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_email_verification_token'),
        ('gouvernance', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profilutilisateur',
            name='province_admin',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='profils_utilisateur',
                to='gouvernance.provadmin',
            ),
        ),
        migrations.AlterField(
            model_name='profilutilisateur',
            name='role',
            field=models.CharField(
                choices=[
                    ('SYSTEM_SUPER_ADMIN', 'Super Admin (Développeur)'),
                    ('INSTITUTION_ADMIN', 'Admin Institution (Secrétaire Général — gestionnaire de données)'),
                    ('MINISTRE', 'Ministre'),
                    ('DIRECTEUR_CABINET', 'Directeur de Cabinet'),
                    ('DIRECTEUR_PROVINCIAL', 'Directeur (Direction provinciale)'),
                    ('INSPECTEUR_GENERAL', 'Inspection générale'),
                ],
                default='INSTITUTION_ADMIN',
                max_length=50,
            ),
        ),
    ]
