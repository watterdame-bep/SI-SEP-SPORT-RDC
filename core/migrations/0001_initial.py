from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('gouvernance', '0004_institution_niveau_territorial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ProfilUtilisateur',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('SYSTEM_SUPER_ADMIN', 'Super Admin (Développeur)'), ('INSTITUTION_ADMIN', 'Admin Institution (Secrétaire Général)')], default='INSTITUTION_ADMIN', max_length=50)),
                ('actif', models.BooleanField(default=True)),
                ('institution', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='profils_utilisateur', to='gouvernance.institution')),
                ('personne', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='profils_utilisateur', to='gouvernance.personne')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profil_sisep', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Profil utilisateur',
                'verbose_name_plural': 'Profils utilisateur',
                'db_table': 'core_profilutilisateur',
            },
        ),
    ]
