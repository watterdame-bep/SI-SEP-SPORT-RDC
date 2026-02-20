"""
Référentiel géographique RDC : Province administrative (ProvAdmin), Territoire/Ville, Secteur/Commune, Groupement/Quartier, Village/Quartier.
Le Territoire/Ville dépend de la Province Administrative (ProvAdmin).
"""
import uuid
from django.db import models


class ProvAdmin(models.Model):
    """Division Provinciale du Sport (Province Administrative)."""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    designation = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    code = models.CharField(max_length=50, unique=True, blank=True)

    class Meta:
        db_table = 'prov_admin'
        verbose_name = 'Division Provinciale'
        verbose_name_plural = 'Divisions Provinciales'

    def __str__(self):
        return self.designation or self.code or str(self.uid)


class TerritoireVille(models.Model):
    """Territoire ou Ville (entité administrative), dépend de la Province Administrative."""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    designation = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    code = models.CharField(max_length=50, unique=True, blank=True)
    province_admin = models.ForeignKey(
        ProvAdmin,
        on_delete=models.PROTECT,
        related_name='territoires_villes',
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'territoire_ville'
        verbose_name = 'Territoire / Ville'
        verbose_name_plural = 'Territoires / Villes'

    def __str__(self):
        return self.designation or self.code or str(self.uid)


class SecteurCommune(models.Model):
    """Secteur ou Commune (sous-territoire)."""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    designation = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    territoire = models.ForeignKey(
        TerritoireVille,
        on_delete=models.PROTECT,
        related_name='secteurs_communes',
    )

    class Meta:
        db_table = 'secteur_commune'
        verbose_name = 'Secteur / Commune'
        verbose_name_plural = 'Secteurs / Communes'

    def __str__(self):
        return self.designation or str(self.uid)


class GroupementQuartier(models.Model):
    """Groupement ou Quartier."""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    designation = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    secteur = models.ForeignKey(
        SecteurCommune,
        on_delete=models.PROTECT,
        related_name='groupements_quartiers',
    )

    class Meta:
        db_table = 'groupement_quartier'
        verbose_name = 'Groupement / Quartier'
        verbose_name_plural = 'Groupements / Quartiers'

    def __str__(self):
        return self.designation or str(self.uid)


class VillageQuartier(models.Model):
    """Village ou Quartier (unité de base pour adresses)."""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    designation = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    groupement = models.ForeignKey(
        GroupementQuartier,
        on_delete=models.PROTECT,
        related_name='villages_quartiers',
    )

    class Meta:
        db_table = 'village_quartier'
        verbose_name = 'Village / Quartier'
        verbose_name_plural = 'Villages / Quartiers'

    def __str__(self):
        return self.designation or str(self.uid)
