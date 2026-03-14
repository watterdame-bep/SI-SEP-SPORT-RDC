# Generated migration to fix ValidationLigue to use DivisionProvinciale

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gouvernance', '0024_add_validation_ligue'),
    ]

    operations = [
        # Remove the old foreign key to Institution
        migrations.RemoveField(
            model_name='validationligue',
            name='division_provinciale',
        ),
        # Add new foreign key to DivisionProvinciale
        migrations.AddField(
            model_name='validationligue',
            name='division_provinciale',
            field=models.ForeignKey(
                help_text='Division Provinciale qui effectue la validation',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='validations_ligues_effectuees',
                to='gouvernance.divisionprovinciale',
                null=True,
                blank=True
            ),
        ),
    ]
