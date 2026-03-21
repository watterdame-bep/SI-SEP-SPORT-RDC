# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gouvernance', '0054_arbitre_photo_empreintes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='arbitre',
            name='niveau',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('PROVINCIAL', 'Provincial'),
                    ('NATIONAL', 'National'),
                    ('INTERNATIONAL', 'International'),
                ],
                default='PROVINCIAL',
            ),
        ),
        migrations.AlterField(
            model_name='arbitre',
            name='categorie',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('STAGIAIRE', 'Stagiaire'),
                    ('ELITE', 'Élite'),
                    ('PROFESSIONNEL', 'Professionnel'),
                ],
                default='STAGIAIRE',
            ),
        ),
    ]
