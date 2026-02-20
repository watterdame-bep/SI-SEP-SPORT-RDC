"""
Personne physique (membres, dirigeants).
"""
import uuid
from django.db import models


class Personne(models.Model):
    """Personne physique (dirigeant, membre d'organigramme)."""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100)
    postnom = models.CharField(max_length=100, blank=True)
    prenom = models.CharField(max_length=100, blank=True)
    sexe = models.CharField(max_length=1, choices=(('M', 'Masculin'), ('F', 'Féminin')), blank=True)
    date_naissance = models.DateField(null=True, blank=True)
    lieu_naissance = models.ForeignKey(
        'gouvernance.TerritoireVille',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='personnes_nees',
    )
    email = models.EmailField(blank=True)
    adresse = models.ForeignKey(
        'gouvernance.AdresseContact',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='personnes',
    )
    photo = models.ImageField(upload_to='personnes/photos/', blank=True, null=True, max_length=500)
    telephone = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = 'personne'
        verbose_name = 'Personne'
        verbose_name_plural = 'Personnes'
        ordering = ['nom', 'postnom', 'prenom']

    def __str__(self):
        return f"{self.nom} {self.postnom} {self.prenom}".strip() or str(self.uid)
