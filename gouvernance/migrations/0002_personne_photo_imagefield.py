# Migration: photo Personne en ImageField

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gouvernance', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='personne',
            name='photo',
            field=models.ImageField(blank=True, max_length=500, null=True, upload_to='personnes/photos/'),
        ),
    ]
