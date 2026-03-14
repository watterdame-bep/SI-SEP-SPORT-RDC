# Generated manually for VisiteMedicale.uid (vérification certificat)

import uuid
from django.db import migrations, models


def gen_uid_for_visites(apps, schema_editor):
    VisiteMedicale = apps.get_model('gouvernance', 'VisiteMedicale')
    for v in VisiteMedicale.objects.all():
        v.uid = uuid.uuid4()
        v.save(update_fields=['uid'])


class Migration(migrations.Migration):

    dependencies = [
        ('gouvernance', '0045_add_medecin_numero_ordre_recommandations_securite'),
    ]

    operations = [
        migrations.AddField(
            model_name='visitemedicale',
            name='uid',
            field=models.UUIDField(editable=False, help_text='Identifiant public pour vérification du certificat (QR code)', null=True, unique=True),
        ),
        migrations.RunPython(gen_uid_for_visites, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='visitemedicale',
            name='uid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, help_text='Identifiant public pour vérification du certificat (QR code)', unique=True),
        ),
    ]
