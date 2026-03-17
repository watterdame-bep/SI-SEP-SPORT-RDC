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
    code_homologation = models.CharField(max_length=50, unique=True, blank=True, null=True)
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

    # Localisation administrative (cascading selects)
    province_admin = models.ForeignKey(
        'gouvernance.ProvAdmin',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='infrastructures',
        help_text='Province administrative où se trouve l\'infrastructure'
    )
    
    territoire = models.ForeignKey(
        'gouvernance.TerritoireVille',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='infrastructures',
    )
    
    secteur = models.ForeignKey(
        'gouvernance.SecteurCommune',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='infrastructures',
    )
    
    quartier = models.ForeignKey(
        'gouvernance.GroupementQuartier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='infrastructures',
    )
    
    # Adresse détaillée
    avenue = models.CharField(
        max_length=255,
        blank=True,
        help_text='Nom de l\'avenue/rue'
    )
    
    numero = models.CharField(
        max_length=50,
        blank=True,
        help_text='Numéro de la rue'
    )

    # Type de propriétaire
    PROPRIETAIRE_TYPE_CHOICES = [
        ('PRIVE', 'Privé'),
        ('PUBLIC', 'Public (État)'),
    ]
    proprietaire_type = models.CharField(
        max_length=50,
        choices=PROPRIETAIRE_TYPE_CHOICES,
        blank=True,
        help_text='Type de propriétaire de l\'infrastructure'
    )
    
    # Type de gestionnaire
    GESTIONNAIRE_TYPE_CHOICES = [
        ('PERSONNE', 'Personne Physique'),
        ('ENTREPRISE', 'Entreprise'),
    ]
    gestionnaire_type = models.CharField(
        max_length=50,
        choices=GESTIONNAIRE_TYPE_CHOICES,
        blank=True,
        help_text='Type de gestionnaire'
    )
    
    # Gestionnaire (détails complets pour les privés)
    gestionnaire_prenom = models.CharField(
        max_length=100,
        blank=True,
        help_text='Prénom du gestionnaire (pour personne physique)'
    )
    
    gestionnaire_nom = models.CharField(
        max_length=100,
        blank=True,
        help_text='Nom du gestionnaire'
    )
    
    gestionnaire_postnom = models.CharField(
        max_length=100,
        blank=True,
        help_text='Postnom du gestionnaire (pour personne physique)'
    )
    
    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]
    gestionnaire_sexe = models.CharField(
        max_length=1,
        choices=SEXE_CHOICES,
        blank=True,
        help_text='Sexe du gestionnaire (pour personne physique)'
    )
    
    # Contact du gestionnaire (téléphone/email)
    telephone_gestionnaire = models.CharField(
        max_length=20,
        blank=True,
        help_text='Numéro de téléphone du gestionnaire'
    )
    
    email_gestionnaire = models.EmailField(
        blank=True,
        help_text='Adresse email du gestionnaire'
    )
    
    # Gestionnaire / propriétaire (texte libre)
    proprietaire = models.CharField(
        max_length=255,
        blank=True,
        help_text='Nom du propriétaire ou de l\'institution propriétaire'
    )

    # Statut de validation
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente de validation'),
        ('VALIDEE', 'Validée'),
        ('REJETEE', 'Rejetée'),
    ]
    statut = models.CharField(
        max_length=50,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE',
        help_text='Statut de validation de l\'infrastructure'
    )
    
    motif_rejet = models.TextField(
        blank=True,
        help_text='Motif du rejet (si applicable)'
    )

    # Suivi technique
    capacite_spectateurs = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Capacité en spectateurs'
    )
    
    surface_sportive = models.CharField(
        max_length=100,
        blank=True,
        help_text='Surface sportive (ex: 100m x 60m, 50m x 25m)'
    )
    
    equipements_disponibles = models.TextField(
        blank=True,
        help_text='Liste des équipements disponibles'
    )
    
    ECLAIRAGE_CHOICES = [
        ('OUI', 'Oui'),
        ('NON', 'Non'),
        ('PARTIEL', 'Partiel'),
    ]
    eclairage = models.CharField(
        max_length=50,
        choices=ECLAIRAGE_CHOICES,
        blank=True,
        help_text='Présence d\'éclairage'
    )
    
    VESTIAIRES_CHOICES = [
        ('OUI', 'Oui'),
        ('NON', 'Non'),
        ('PARTIEL', 'Partiel'),
    ]
    vestiaires = models.CharField(
        max_length=50,
        choices=VESTIAIRES_CHOICES,
        blank=True,
        help_text='Présence de vestiaires'
    )
    
    securite = models.TextField(
        blank=True,
        help_text='Mesures de sécurité en place'
    )
    
    ETAT_VIABILITE_CHOICES = [
        ('OPERATIONNEL', 'Opérationnel'),
        ('EN_TRAVAUX', 'En travaux'),
        ('IMPRATICABLE', 'Impraticable'),
    ]
    etat_viabilite = models.CharField(
        max_length=50,
        choices=ETAT_VIABILITE_CHOICES,
        default='OPERATIONNEL',
        blank=True,
        help_text='État de viabilité de l\'infrastructure'
    )

    # Type de sol
    TYPE_SOL_CHOICES = [
        ('SYNTHETIQUE', 'Synthétique'),
        ('GAZON', 'Gazon'),
        ('TERRE_BATTUE', 'Terre battue'),
        ('BETON', 'Béton'),
        ('AUTRE', 'Autre'),
    ]
    type_sol = models.CharField(
        max_length=50,
        choices=TYPE_SOL_CHOICES,
        blank=True,
        help_text='Type de sol de l\'infrastructure'
    )

    # Infrastructure d'intérêt national (modifiable uniquement par SG)
    interet_national = models.BooleanField(
        default=False,
        help_text='Infrastructure d\'intérêt national (modifiable uniquement par SG)'
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


class PhotoInfrastructure(models.Model):
    """Photos du stade/infrastructure (5 photos obligatoires)."""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    infrastructure = models.ForeignKey(
        Infrastructure,
        on_delete=models.CASCADE,
        related_name='photos',
    )
    photo = models.ImageField(
        upload_to='infrastructures/photos/',
        help_text='Photo du stade'
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        help_text='Description de la photo (ex: Vue générale, Entrée, Vestiaires, etc.)'
    )
    date_upload = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'photo_infrastructure'
        verbose_name = 'Photo infrastructure'
        verbose_name_plural = 'Photos infrastructure'
        ordering = ['date_upload']
    
    def __str__(self):
        return f"Photo - {self.infrastructure.nom}"


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


class MaintenanceLog(models.Model):
    """Journal de maintenance d'une infrastructure."""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    infrastructure = models.ForeignKey(
        Infrastructure,
        on_delete=models.CASCADE,
        related_name='maintenance_logs',
    )
    date_intervention = models.DateField()
    type_intervention = models.CharField(
        max_length=100,
        help_text='Ex: Tonte, Réparation filets, Nettoyage vestiaires'
    )
    description = models.TextField(help_text='Détails de l\'intervention')
    photo = models.ImageField(
        upload_to='infrastructures/maintenance/',
        null=True,
        blank=True,
        help_text='Photo avant/après de l\'intervention'
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'maintenance_log'
        verbose_name = 'Journal de maintenance'
        verbose_name_plural = 'Journaux de maintenance'
        ordering = ['-date_intervention']

    def __str__(self):
        return f"{self.infrastructure} - {self.type_intervention} ({self.date_intervention})"


class StateChangeLog(models.Model):
    """Historique des changements d'état d'une infrastructure."""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    infrastructure = models.ForeignKey(
        Infrastructure,
        on_delete=models.CASCADE,
        related_name='state_changes',
    )
    ancien_etat = models.CharField(max_length=50)
    nouvel_etat = models.CharField(max_length=50)
    justification = models.TextField(help_text='Raison du changement d\'état')
    photo = models.ImageField(
        upload_to='infrastructures/incidents/',
        null=True,
        blank=True,
        help_text='Photo de l\'incident (si applicable)'
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'state_change_log'
        verbose_name = 'Changement d\'état'
        verbose_name_plural = 'Changements d\'état'
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.infrastructure} - {self.ancien_etat} → {self.nouvel_etat}"


class ReservationSlot(models.Model):
    """Créneaux de réservation pour une infrastructure."""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    infrastructure = models.ForeignKey(
        Infrastructure,
        on_delete=models.CASCADE,
        related_name='reservations',
    )
    club = models.ForeignKey(
        'gouvernance.Institution',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='infrastructure_reservations',
    )
    date_reservation = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    present = models.BooleanField(default=False, help_text='Club présent à la réservation')
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reservation_slot'
        verbose_name = 'Créneau de réservation'
        verbose_name_plural = 'Créneaux de réservation'
        ordering = ['date_reservation', 'heure_debut']
        unique_together = ['infrastructure', 'date_reservation', 'heure_debut', 'heure_fin']

    def __str__(self):
        return f"{self.infrastructure} - {self.date_reservation} {self.heure_debut}-{self.heure_fin}"


# ---------- Billetterie numérique (anti-fraude, traçabilité des recettes) ----------

class Evenement(models.Model):
    """
    Événement sportif (match, compétition d'athlétisme, etc.) se tenant dans une infrastructure.
    Lieu = stade (Infrastructure). Lié au module compétition.
    L'organisateur (ligue, fédération, etc.) peut être renseigné pour le suivi.
    """
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    infrastructure = models.ForeignKey(
        Infrastructure,
        on_delete=models.PROTECT,
        related_name='evenements',
        help_text='Lieu (stade) de l\'événement',
    )
    organisateur = models.ForeignKey(
        'gouvernance.Institution',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evenements_organises',
        help_text='Ligue ou fédération organisatrice (ex: ligue provinciale)',
    )
    titre = models.CharField(max_length=255, help_text='Ex: Match RDC vs Sénégal, Championnat d\'athlétisme')
    type_evenement = models.CharField(
        max_length=50,
        choices=[
            ('MATCH', 'Match'),
            ('COMPETITION_ATHLETISME', 'Compétition d\'athlétisme'),
            ('COMPETITION', 'Compétition sportive'),
            ('GALA', 'Gala / Cérémonie'),
            ('RESERVATION', 'Réservation privée'),
            ('AUTRE', 'Autre'),
        ],
        default='MATCH',
    )
    date_evenement = models.DateField()
    heure_debut = models.TimeField(null=True, blank=True)
    description = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    actif = models.BooleanField(default=True)

    class Meta:
        db_table = 'evenement'
        verbose_name = 'Événement'
        verbose_name_plural = 'Événements'
        ordering = ['-date_evenement', '-heure_debut']

    def __str__(self):
        return f"{self.titre} — {self.date_evenement} ({self.infrastructure.nom})"


class ZoneStade(models.Model):
    """
    Zone du stade (Tribune d'honneur, Tribune latérale, Pourtour, etc.).
    Chaque zone peut avoir un prix différent par événement (voir EvenementZone).
    """
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    infrastructure = models.ForeignKey(
        Infrastructure,
        on_delete=models.CASCADE,
        related_name='zones',
        help_text='Stade concerné',
    )
    nom = models.CharField(max_length=100, help_text='Ex: Tribune d\'honneur, Tribune latérale, Pourtour')
    ordre = models.PositiveSmallIntegerField(default=0, help_text='Ordre d\'affichage')

    class Meta:
        db_table = 'zone_stade'
        verbose_name = 'Zone stade'
        verbose_name_plural = 'Zones stade'
        ordering = ['infrastructure', 'ordre', 'nom']
        unique_together = [['infrastructure', 'nom']]

    def __str__(self):
        return f"{self.nom} — {self.infrastructure.nom}"


class EvenementZone(models.Model):
    """
    Tarif et capacité par zone pour un événement donné.
    Une même zone (ex: Tribune d'honneur) peut avoir un prix et une capacité max par événement.
    """
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evenement = models.ForeignKey(
        Evenement,
        on_delete=models.CASCADE,
        related_name='zones_tarifs',
    )
    zone_stade = models.ForeignKey(
        ZoneStade,
        on_delete=models.PROTECT,
        related_name='evenements_tarifs',
    )
    prix_unitaire = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Prix du ticket pour cette zone (CDF)',
    )
    devise = models.CharField(max_length=3, default='CDF')
    capacite_max = models.PositiveIntegerField(
        help_text='Nombre de places (tickets) disponibles pour cette zone',
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'evenement_zone'
        verbose_name = 'Tarif zone (événement)'
        verbose_name_plural = 'Tarifs zones (événement)'
        unique_together = [['evenement', 'zone_stade']]

    def __str__(self):
        return f"{self.evenement.titre} — {self.zone_stade.nom}: {self.prix_unitaire} {self.devise}"

    def generer_tickets(self):
        """Crée les tickets disponibles pour cette zone (jusqu'à capacite_max)."""
        existants = self.tickets.count()
        a_creer = self.capacite_max - existants
        if a_creer <= 0:
            return 0
        for _ in range(a_creer):
            Ticket.objects.create(evenement_zone=self, statut='DISPONIBLE')
        return a_creer


class Vente(models.Model):
    """
    Vente de un ou plusieurs tickets. Traçabilité : date, montant, canal (Guichet ou Mobile Money).
    """
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evenement = models.ForeignKey(
        Evenement,
        on_delete=models.PROTECT,
        related_name='ventes',
    )
    date_vente = models.DateTimeField(auto_now_add=True)
    montant_total = models.DecimalField(max_digits=14, decimal_places=2)
    devise = models.CharField(max_length=3, default='CDF')
    canal = models.CharField(
        max_length=50,
        choices=[
            ('GUICHET', 'Guichet'),
            ('MOBILE_MONEY', 'Mobile Money'),
            ('EN_LIGNE', 'En ligne'),
            ('AUTRE', 'Autre'),
        ],
        default='GUICHET',
    )
    reference_paiement = models.CharField(
        max_length=255,
        blank=True,
        help_text='Référence transaction (ex: Mobile Money)',
    )
    acheteur_nom = models.CharField(max_length=255, blank=True)
    acheteur_telephone = models.CharField(max_length=20, blank=True)
    caissier = models.ForeignKey(
        'core.ProfilUtilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ventes_billetterie',
    )
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'vente_billetterie'
        verbose_name = 'Vente (billetterie)'
        verbose_name_plural = 'Ventes (billetterie)'
        ordering = ['-date_vente']

    def __str__(self):
        return f"Vente {self.date_vente.strftime('%d/%m/%Y %H:%M')} — {self.montant_total} {self.devise}"


class Ticket(models.Model):
    """
    Ticket avec code unique (UUID) et QR Code pour lutte anti-fraude.
    Chaque ticket est unique ; une fois utilisé (scanné à l'entrée), il ne peut plus servir.
    """
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_billet = models.CharField(
        max_length=12,
        unique=True,
        null=True,
        blank=True,
        editable=False,
        help_text='Numéro de billet visible (pour vérification manuelle)'
    )
    evenement_zone = models.ForeignKey(
        EvenementZone,
        on_delete=models.PROTECT,
        related_name='tickets',
    )
    vente = models.ForeignKey(
        Vente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets',
        help_text='Vente associée (null si pas encore vendu)',
    )
    statut = models.CharField(
        max_length=20,
        choices=[
            ('DISPONIBLE', 'Disponible'),
            ('EN_RESERVATION', 'En réservation (paiement en cours)'),
            ('RESERVE', 'Réservé (en attente de paiement)'),
            ('VENDU', 'Vendu'),
            ('UTILISE', 'Utilisé (scanné à l\'entrée)'),
            ('ANNULE', 'Annulé'),
        ],
        default='DISPONIBLE',
    )
    date_utilisation = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Date/heure du scan à l\'entrée (anti-fraude)',
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ticket_billetterie'
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        ordering = ['evenement_zone', 'date_creation']

    def save(self, *args, **kwargs):
        # Générer un numéro de billet unique si pas encore défini
        if not self.numero_billet:
            self.numero_billet = self.generer_numero_billet()
        super().save(*args, **kwargs)

    def generer_numero_billet(self):
        """Génère un numéro de billet unique de 12 caractères"""
        import random
        import string
        
        # Format: TKT + 8 chiffres aléatoires
        while True:
            numero = 'TKT' + ''.join(random.choices(string.digits, k=8))
            if not Ticket.objects.filter(numero_billet=numero).exists():
                return numero

    def generer_qr_code(self):
        """Génère le QR code pour le ticket"""
        import qrcode
        from io import BytesIO
        import base64
        
        # Données à encoder dans le QR code
        qr_data = {
            'ticket_uid': str(self.uid),
            'numero_billet': self.numero_billet,
            'evenement': self.evenement_zone.evenement.titre,
            'date_evenement': self.evenement_zone.evenement.date_evenement.strftime('%Y-%m-%d'),
            'zone': self.evenement_zone.zone_stade.nom,
            'stade': self.evenement_zone.evenement.infrastructure.nom
        }
        
        # Créer le QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(str(qr_data))
        qr.make(fit=True)
        
        # Générer l'image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir en base64 pour l'affichage web
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"

    def get_qr_url(self):
        """Retourne l'URL publique pour afficher le ticket"""
        return f"/ticket/{self.uid}/"

    def __str__(self):
        return f"Ticket {self.numero_billet} — {self.get_statut_display()}"

    @property
    def evenement(self):
        return self.evenement_zone.evenement

    @property
    def zone_stade(self):
        return self.evenement_zone.zone_stade

    def get_verification_url(self, request=None):
        """URL de vérification du ticket (à encoder en QR code)."""
        from django.urls import reverse
        path = reverse('infrastructures:verifier_ticket', kwargs={'ticket_uid': self.uid})
        if request:
            return request.build_absolute_uri(path)
        return path
