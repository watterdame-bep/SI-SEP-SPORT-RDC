# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gouvernance', '0053_arbitre_workflow_medical'),
    ]

    operations = [
        migrations.AddField(
            model_name='arbitre',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to='arbitres/photos/'),
        ),
        migrations.AddField(
            model_name='arbitre',
            name='empreintes_template',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='arbitre',
            name='empreintes_capturees',
            field=models.BooleanField(default=False),
        ),
    ]
