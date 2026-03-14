"""
Organigramme : Fonctions, Membres, Mandats (mandats des membres des institutions).
"""
import uuid
from django.db import models


class Fonction(models.Model):
    """Fonction dans l'organigramme (Président, Secrétaire, Trésorier, etc.)."""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    designation = models.CharField(max_length=150)
    ordre_priorite = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'fonction'
        verbose_name = 'Fonction'
        verbose_name_plural = 'Fonctions'
        ordering = ['ordre_priorite', 'designation']

    def __str__(self):
        return self.designation or str(self.uid)


class Membre(models.Model):
    """Membre d'une institution (lien Personne - Institution - Fonction)."""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    personne = models.ForeignKey(
        'gouvernance.Personne',
        on_delete=models.CASCADE,
        related_name='membres',
    )
    institution = models.ForeignKey(
        'gouvernance.Institution',
        on_delete=models.CASCADE,
        related_name='membres',
    )
    fonction = models.ForeignKey(
        Fonction,
        on_delete=models.PROTECT,
        related_name='membres',
    )

    class Meta:
        db_table = 'membre'
        verbose_name = 'Membre'
        verbose_name_plural = 'Membres'
        unique_together = [['personne', 'institution', 'fonction']]

    def __str__(self):
        return f"{self.personne} - {self.fonction} @ {self.institution}"


class Mandat(models.Model):
    """Mandat d'un membre (période, statut, document de nomination). La fonction et l'institution viennent du membre."""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    membre = models.ForeignKey(
        Membre,
        on_delete=models.CASCADE,
        related_name='mandats',
    )
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    statut_mandat = models.CharField(max_length=50, blank=True)  # En cours, Terminé, Révoqué...
    docum_nomination_url = models.URLField(max_length=500, blank=True)

    class Meta:
        db_table = 'mandat'
        verbose_name = 'Mandat'
        verbose_name_plural = 'Mandats'
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.membre} ({self.date_debut} - {self.date_fin or '?'})"

    @property
    def institution(self):
        """Institution du mandat (via le membre)."""
        return self.membre.institution

    @property
    def fonction(self):
        """Fonction du mandat (via le membre)."""
        return self.membre.fonction
