"""
Institutions sportives : hiérarchie avec Institution Parente (tutelle).
État -> Fédérations -> Ligues -> Clubs.
Le Ministère est l'unique nœud sans parent (institution_tutelle=NULL).
"""
import uuid
from django.db import models

NIVEAU_TERRITORIAL_CHOICES = [
    ('NATIONAL', 'National'),           # Ministère
    ('PROVINCIAL', 'Provincial'),      # Division Provinciale
    ('FEDERATION', 'Fédération'),      # Fédération nationale
    ('LIGUE', 'Ligue'),
    ('CLUB', 'Club'),
]


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

    # Institution parente (tutelle) — relation auto-référente. NULL uniquement pour le Ministère (racine).
    institution_tutelle = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='institutions_fille',
    )
    # Niveau territorial (NATIONAL pour le Ministère, PROVINCIAL pour Divisions, etc.)
    niveau_territorial = models.CharField(
        max_length=20,
        choices=NIVEAU_TERRITORIAL_CHOICES,
        default='CLUB',
        db_index=True,
    )

    email_officiel = models.EmailField(blank=True)
    telephone_off = models.CharField(max_length=50, blank=True)

    # Logo (optionnel ; utilisé notamment pour le Ministère)
    logo = models.ImageField(upload_to='institutions/logos/', blank=True, null=True, max_length=500)

    # Statut pour l'institution mère : ACTIVE et VALIDÉE par défaut au setup
    statut_activation = models.CharField(
        max_length=20,
        choices=[('ACTIVE', 'Active'), ('INACTIF', 'Inactif')],
        default='ACTIVE',
        blank=True,
        db_index=True,
    )
    statut_validee = models.BooleanField(default=False)

    # Workflow signature Ministre : Fédérations créées par le SG apparaissent en ATTENTE_SIGNATURE
    STATUT_SIGNATURE_CHOICES = [
        ('', '—'),
        ('ATTENTE_SIGNATURE', 'En attente de signature'),
        ('SIGNE', 'Signé'),
        ('REFUSE', 'Refusé'),
    ]
    statut_signature = models.CharField(
        max_length=30,
        choices=STATUT_SIGNATURE_CHOICES,
        blank=True,
        default='',
        db_index=True,
    )

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

    @property
    def is_racine(self):
        """True si c'est l'institution mère (Ministère), sans parent."""
        return self.institution_tutelle_id is None
