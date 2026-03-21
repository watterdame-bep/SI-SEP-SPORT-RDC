# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gouvernance', '0052_add_arbitre_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='arbitre',
            name='resultat_medical',
            field=models.CharField(
                max_length=20,
                choices=[('APTE', 'Apte'), ('INAPTE', 'Inapte'), ('APTE_AVEC_RESERVE', 'Apte avec réserve')],
                null=True,
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name='arbitre',
            name='notes_medicales',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='arbitre',
            name='date_examen_medical',
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='arbitre',
            name='statut',
            field=models.CharField(
                max_length=30,
                choices=[
                    ('EN_ATTENTE_MEDICALE', 'En attente médicale'),
                    ('INSTRUIT', 'Instruit (médical OK)'),
                    ('INAPTE', 'Inapte (médical)'),
                    ('ACTIF', 'Actif (licence délivrée)'),
                    ('SUSPENDU', 'Suspendu'),
                    ('INACTIF', 'Inactif'),
                ],
                default='EN_ATTENTE_MEDICALE',
            ),
        ),
    ]
