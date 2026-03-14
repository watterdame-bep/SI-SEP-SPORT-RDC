# Migration: niveau_territorial sur Institution (NATIONAL pour le Ministère)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gouvernance', '0003_mandat_lie_uniquement_a_membre'),
    ]

    operations = [
        migrations.AddField(
            model_name='institution',
            name='niveau_territorial',
            field=models.CharField(
                choices=[
                    ('NATIONAL', 'National'),
                    ('PROVINCIAL', 'Provincial'),
                    ('FEDERATION', 'Fédération'),
                    ('LIGUE', 'Ligue'),
                    ('CLUB', 'Club'),
                ],
                db_index=True,
                default='CLUB',
                max_length=20,
            ),
        ),
    ]
