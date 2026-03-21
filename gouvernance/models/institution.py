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
    
    # Numéro de dossier interne pour le suivi
    numero_dossier = models.CharField(max_length=100, blank=True, help_text="Numéro de dossier interne")
    
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
    site_web = models.URLField(max_length=500, blank=True, help_text="Site web officiel")

    # Logo (optionnel ; utilisé notamment pour le Ministère)
    logo = models.ImageField(upload_to='institutions/logos/', blank=True, null=True, max_length=500)
    
    # Informations sur l'agrément
    type_agrement_sollicite = models.CharField(
        max_length=50,
        choices=[('PROVISOIRE', 'Provisoire'), ('DEFINITIF', 'Définitif')],
        blank=True,
        help_text="Type d'agrément sollicité"
    )
    date_demande_agrement = models.DateField(null=True, blank=True, help_text="Date de demande d'agrément")
    duree_sollicitee = models.PositiveIntegerField(default=4, help_text="Durée sollicitée en années (olympiade)")
    
    # Responsables (Bureau Provisoire)
    nom_president = models.CharField(max_length=255, blank=True, help_text="Nom du Président/Mandataire")
    telephone_president = models.CharField(max_length=50, blank=True, help_text="Téléphone du responsable")
    
    # Documents joints
    document_statuts = models.FileField(upload_to='institutions/documents/', blank=True, null=True, max_length=500, help_text="Statuts de la fédération (PDF)")
    document_pv_ag = models.FileField(upload_to='institutions/documents/', blank=True, null=True, max_length=500, help_text="PV de l'AG Constitutive (PDF)")
    document_liste_membres = models.FileField(upload_to='institutions/documents/', blank=True, null=True, max_length=500, help_text="Liste des membres du comité (PDF)")
    document_certificat = models.FileField(upload_to='institutions/documents/', blank=True, null=True, max_length=500, help_text="Certificat de recherche (PDF)")
    document_reglement_interieur = models.FileField(upload_to='institutions/documents/', blank=True, null=True, max_length=500, help_text="Règlement intérieur du club (PDF)")
    document_contrat_bail = models.FileField(upload_to='institutions/documents/', blank=True, null=True, max_length=500, help_text="Contrat de bail du club (PDF)")
    document_certificat_nationalite = models.FileField(upload_to='institutions/documents/', blank=True, null=True, max_length=500, help_text="Certificat de nationalité du responsable (PDF)")
    document_liste_athletes = models.FileField(upload_to='institutions/documents/', blank=True, null=True, max_length=500, help_text="Liste des athlètes du club (PDF)")

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
    
    # Workflow inspection provinciale : Fédérations doivent passer par inspection avant signature
    STATUT_INSPECTION_CHOICES = [
        ('', '—'),
        ('AUDIT', 'Audit'),
        ('PROVINCE_RENDU', 'Province rendu'),
        ('ATTENTE_AGREMENT', 'Attente agrément'),
        ('EN_INSPECTION', 'En inspection provinciale'),  # legacy — ligues uniquement
        ('INSPECTION_VALIDEE', 'Inspection validée'),
        ('INSPECTION_REJETEE', 'Inspection rejetée'),
    ]
    statut_inspection = models.CharField(
        max_length=30,
        choices=STATUT_INSPECTION_CHOICES,
        blank=True,
        default='',
        db_index=True,
        help_text='Statut de l\'inspection provinciale pour les fédérations'
    )
    
    # Arrêté Ministériel d'Agrément (généré automatiquement lors de la signature)
    numero_arrete = models.CharField(max_length=100, blank=True, help_text="Numéro de l'arrêté ministériel (ex: N°001/MIN/SL/2026)")
    date_signature_arrete = models.DateTimeField(null=True, blank=True, help_text="Date et heure de signature de l'arrêté")
    document_arrete = models.FileField(upload_to='institutions/arretes/', blank=True, null=True, max_length=500, help_text="Arrêté ministériel d'agrément (PDF)")
    arrete_vu_par_sg = models.BooleanField(default=False, help_text="Indique si le SG a déjà consulté cet arrêté")

    # Certificat d'Homologation Nationale (généré automatiquement lors de la signature)
    numero_homologation = models.CharField(max_length=100, blank=True, help_text="Numéro d'homologation du certificat (ex: RDC/MIN-SPORT/FED/2026-001)")
    document_certificat_homologation = models.FileField(upload_to='institutions/certificats/', blank=True, null=True, max_length=500, help_text="Certificat d'Homologation Nationale (PDF)")
    date_generation_certificat = models.DateTimeField(null=True, blank=True, help_text="Date de génération du certificat")

    # Lien vers l'agrément administratif (validation Division Provinciale)
    etat_administrative = models.OneToOneField(
        'gouvernance.EtatAdministrative',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='institution',
    )
    
    # Province Administrative (pour les Divisions Provinciales)
    province_admin = models.ForeignKey(
        'gouvernance.ProvAdmin',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='divisions',
        help_text="Province Administrative associée à cette Division Provinciale"
    )
    
    # Disciplines sportives (pour les Fédérations uniquement)
    disciplines = models.ManyToManyField(
        'gouvernance.DisciplineSport',
        blank=True,
        related_name='federations',
        help_text="Disciplines sportives gérées par cette fédération",
    )
    
    # Provinces d'implantation (pour les Fédérations uniquement)
    # Les provinces où la fédération prétend être installée
    provinces_implantation = models.ManyToManyField(
        'gouvernance.ProvAdmin',
        blank=True,
        related_name='federations_implantees',
        help_text="Provinces où la fédération prétend être installée",
    )
    
    # Signature et Cachet (pour les Ligues et Fédérations)
    signature_image = models.ImageField(
        upload_to='institutions/signatures/',
        blank=True,
        null=True,
        max_length=500,
        help_text="Signature numérique de la ligue/fédération (PNG transparent)"
    )
    sceau_image = models.ImageField(
        upload_to='institutions/sceaux/',
        blank=True,
        null=True,
        max_length=500,
        help_text="Cachet/Sceau de la ligue/fédération (PNG transparent)"
    )
    
    # Club Validation Workflow (pour les Clubs)
    STATUT_VALIDATION_CLUB_CHOICES = [
        ('', '—'),
        ('EN_ATTENTE_VALIDATION', 'En attente de validation provinciale'),
        ('VALIDEE_PROVINCIALE', 'Validée par la direction provinciale'),
        ('REJETEE_PROVINCIALE', 'Rejetée par la direction provinciale'),
        ('AFFILIEE', 'Affiliée (officielle)'),
    ]
    statut_validation_club = models.CharField(
        max_length=50,
        choices=STATUT_VALIDATION_CLUB_CHOICES,
        default='',
        blank=True,
        db_index=True,
        help_text='Statut de validation du club par la direction provinciale'
    )
    
    existence_physique_confirmee = models.BooleanField(
        default=False,
        help_text='Existence physique du club confirmée par la direction provinciale'
    )
    
    # Club Affiliation (pour les Clubs)
    numero_affiliation = models.CharField(
        max_length=100,
        blank=True,
        help_text="Numéro d'affiliation unique (ex: A-2026-FÉDÉ-PROV-001)"
    )
    date_affiliation = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date et heure de l'affiliation officielle"
    )
    document_acte_affiliation = models.FileField(
        upload_to='institutions/actes_affiliation/',
        blank=True,
        null=True,
        max_length=500,
        help_text="Acte d'Affiliation Provincial (PDF)"
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
