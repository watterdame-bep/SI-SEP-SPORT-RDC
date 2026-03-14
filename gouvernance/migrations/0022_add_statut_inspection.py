# Generated migration for adding statut_inspection field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gouvernance', '0021_institution_provinces_implantation_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='institution',
            name='statut_inspection',
            field=models.CharField(
                max_length=30,
                choices=[
                    ('', '—'),
                    ('EN_INSPECTION', 'En inspection provinciale'),
                    ('INSPECTION_VALIDEE', 'Inspection validée'),
                    ('INSPECTION_REJETEE', 'Inspection rejetée'),
                ],
                blank=True,
                default='',
                db_index=True,
                help_text='Statut de l\'inspection provinciale pour les fédérations'
            ),
        ),
    ]
