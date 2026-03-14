# Migration: Mandat lié uniquement à Membre (fonction et institution via membre)

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gouvernance', '0002_personne_photo_imagefield'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mandat',
            name='fonction',
        ),
        migrations.RemoveField(
            model_name='mandat',
            name='institution',
        ),
    ]
