"""
Module Infrastructures - SI-SEP Sport RDC.
Registre national des stades/terrains, géolocalisation, suivi technique et revenus.
Codes d'homologation uniques (souveraineté des données).
"""
import uuid
from django.db import models


class TypeInfrastructure(models.Model):
    """Type d'infrastructure (Stade, Terrain, Salle, Piscine, etc.)."""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    designation = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True, blank=True)

    class Meta:
        db_table = 'type_infrastructure'
        verbose_name = 'Type d\'infrastructure'
        verbose_name_plural = 'Types d\'infrastructure'

    def __str__(self):
        return self.designation or self.code or str(self.uid)


class Infrastructure(models.Model):
    """
    Registre national des stades et terrains.
    Code d'homologation unique, géolocalisation (coordonnées GPS).
    """
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Code d'homologation unique (souveraineté des données)
    code_homologation = models.CharField(max_length=50, unique=True)
    nom = models.CharField(max_length=255)
    type_infrastructure = models.ForeignKey(
        TypeInfrastructure,
        on_delete=models.PROTECT,
        related_name='infrastructures',
    )
    description = models.TextField(blank=True)

    # Géolocalisation (coordonnées GPS)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Latitude (ex: -4.321000)",
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Longitude (ex: 15.312500)",
    )
    adresse_texte = models.CharField(max_length=500, blank=True)

    # Localisation administrative (optionnel, lien avec référentiel gouvernance)
    territoire = models.ForeignKey(
        'gouvernance.TerritoireVille',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='infrastructures',
    )

    # Gestionnaire / propriétaire (institution éventuelle)
    gestionnaire = models.ForeignKey(
        'gouvernance.Institution',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='infrastructures_gerees',
    )

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    actif = models.BooleanField(default=True)

    class Meta:
        db_table = 'infrastructure'
        verbose_name = 'Infrastructure sportive'
        verbose_name_plural = 'Infrastructures sportives'
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.code_homologation})"


class SuiviTechnique(models.Model):
    """Suivi technique d'une infrastructure (état, travaux, capacité, etc.)."""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    infrastructure = models.ForeignKey(
        Infrastructure,
        on_delete=models.CASCADE,
        related_name='suivis_techniques',
    )
    date_controle = models.DateField()
    etat_general = models.CharField(max_length=50, blank=True)  # Bon, Moyen, Dégradé...
    capacite_spectateurs = models.PositiveIntegerField(null=True, blank=True)
    observations = models.TextField(blank=True)
    rapport_url = models.URLField(max_length=500, blank=True)

    class Meta:
        db_table = 'suivi_technique'
        verbose_name = 'Suivi technique'
        verbose_name_plural = 'Suivis techniques'
        ordering = ['-date_controle']

    def __str__(self):
        return f"{self.infrastructure} - {self.date_controle}"


class RevenuInfrastructure(models.Model):
    """Revenus générés par une infrastructure (location, billetterie, etc.)."""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    infrastructure = models.ForeignKey(
        Infrastructure,
        on_delete=models.CASCADE,
        related_name='revenus',
    )
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    type_revenu = models.CharField(max_length=100, blank=True)  # Location, Billetterie...
    montant = models.DecimalField(max_digits=14, decimal_places=2)
    devise = models.CharField(max_length=3, default='CDF')
    libelle = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'revenu_infrastructure'
        verbose_name = 'Revenu infrastructure'
        verbose_name_plural = 'Revenus infrastructures'
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.infrastructure} - {self.montant} {self.devise} ({self.date_debut})"
