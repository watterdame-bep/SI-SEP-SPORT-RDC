"""
Adresses de contact (avec coordonnées GPS — souveraineté des données).
"""
import uuid
from django.db import models


class AdresseContact(models.Model):
    """Adresse physique avec géolocalisation (coordonnées GPS)."""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    avenue = models.CharField(max_length=255, blank=True)
    numero = models.PositiveIntegerField(null=True, blank=True)
    quartier_village = models.ForeignKey(
        'gouvernance.VillageQuartier',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='adresses',
    )
    gps = models.CharField(max_length=100, blank=True, help_text="Coordonnées GPS (lat, lon)")  
    institution = models.ForeignKey(
        'gouvernance.Institution',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='adresses_contact',
    )

    class Meta:
        db_table = 'adresse_contact'
        verbose_name = 'Adresse de contact'
        verbose_name_plural = 'Adresses de contact'

    def __str__(self):
        return f"{self.avenue or 'N/A'} {self.numero or ''}".strip() or str(self.uid)
