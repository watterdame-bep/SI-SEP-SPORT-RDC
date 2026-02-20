"""
Institutions sportives : hiérarchie avec Institution Parente (tutelle).
État -> Fédérations -> Ligues -> Clubs.
"""
import uuid
from django.db import models


class TypeInstitution(models.Model):
    """Type d'institution (Ministère, Division Provinciale, Fédération, Ligue, Club, etc.)."""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    designation = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True, blank=True)

    class Meta:
        db_table = 'type_institution'
        verbose_name = 'Type d\'institution'
        verbose_name_plural = 'Types d\'institution'

    def __str__(self):
        return self.designation or self.code or str(self.uid)


class Institution(models.Model):
    """
    Institution du mouvement sportif.
    Chaque institution peut avoir une institution parente (tutelle) pour la hiérarchie.
    """
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    nom_officiel = models.CharField(max_length=255)
    sigle = models.CharField(max_length=50, blank=True)
    type_institution = models.ForeignKey(
        TypeInstitution,
        on_delete=models.PROTECT,
        related_name='institutions',
    )
    statut_juridique = models.CharField(max_length=100, blank=True)
    date_creation = models.DateField(null=True, blank=True)

    nombre_pers_admin = models.PositiveIntegerField(default=0)
    nombre_pers_tech = models.PositiveIntegerField(default=0)
    partenaire = models.CharField(max_length=255, blank=True)

    # Institution parente (tutelle) — relation auto-référente pour la hiérarchie
    institution_tutelle = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='institutions_fille',
    )

    email_officiel = models.EmailField(blank=True)
    telephone_off = models.CharField(max_length=50, blank=True)

    # Lien vers l'agrément administratif (validation Division Provinciale)
    etat_administrative = models.OneToOneField(
        'gouvernance.EtatAdministrative',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='institution',
    )

    class Meta:
        db_table = 'institution'
        verbose_name = 'Institution'
        verbose_name_plural = 'Institutions'
        ordering = ['nom_officiel']

    def __str__(self):
        return f"{self.nom_officiel} ({self.sigle or self.code})"
