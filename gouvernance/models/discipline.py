"""
Disciplines sportives reconnues en RDC (Football, Basket-ball, etc.).
Référentiel utilisé pour les fédérations et les listes de choix.
"""
import uuid
from django.db import models


class DisciplineSport(models.Model):
    """Discipline sportive reconnue en RDC (ex. Football, Basket-ball, Athlétisme)."""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    designation = models.CharField(max_length=255)
    ordre = models.PositiveSmallIntegerField(
        default=0,
        help_text="Ordre d'affichage dans les listes",
    )
    actif = models.BooleanField(default=True)

    class Meta:
        db_table = 'discipline_sport'
        verbose_name = 'Discipline sportive'
        verbose_name_plural = 'Disciplines sportives'
        ordering = ['ordre', 'designation']

    def __str__(self):
        return self.designation or self.code or str(self.uid)
