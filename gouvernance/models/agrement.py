"""
Agréments : validation à double niveau (Sportif via Ligue/Fédé, Administratif via Division Provinciale).
"""
import uuid
from django.db import models


class EtatAgrement(models.Model):
    """État de l'agrément (En attente, Accordé, Refusé, Révoqué, etc.)."""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    designation = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True, blank=True)

    class Meta:
        db_table = 'etat_agrement'
        verbose_name = 'État d\'agrément'
        verbose_name_plural = 'États d\'agrément'

    def __str__(self):
        return self.designation or self.code or str(self.uid)


class EtatAdministrative(models.Model):
    """
    Agrément administratif délivré par la Division Provinciale.
    Double validation : validation_admin (Division Prov.) et valid_tec_sportive (Ligue/Fédé).
    """
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    num_agrement_admin = models.CharField(max_length=100, unique=True)
    date_delivrance = models.DateField(null=True, blank=True)
    etat_agrement = models.ForeignKey(
        EtatAgrement,
        on_delete=models.PROTECT,
        related_name='etats_administratifs',
    )
    est_affiliee = models.CharField(max_length=255, blank=True)
    docum_agrement_url = models.URLField(max_length=500, blank=True)

    # Validation à double niveau
    validation_admin = models.CharField(max_length=50, blank=True)   # Division Provinciale
    valid_tec_sportive = models.CharField(max_length=50, blank=True)  # Ligue / Fédération

    class Meta:
        db_table = 'etat_administrative'
        verbose_name = 'Agrément administratif'
        verbose_name_plural = 'Agréments administratifs'

    def __str__(self):
        return f"{self.num_agrement_admin} ({self.etat_agrement})"
