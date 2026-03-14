# -*- coding: utf-8 -*-
"""
Modèle Athlete pour la gestion des athlètes des clubs.
Conforme aux fiches F05 (Fiche Athlète National), F21 (Profil Athlète), 
F22 (Identification Sportive), F29 et F32 (Santé et Protection).
"""
import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date


class Athlete(models.Model):
    """
    Athlète inscrit dans un club sportif.
    Utilise le modèle Personne pour les informations d'identité civile (F05, F21).
    """
    CATEGORIE_CHOICES = [
        ('SENIOR', 'Senior'),
        ('JUNIOR', 'Junior (U20)'),
        ('CADET', 'Cadet (U17)'),
        ('MINIME', 'Minime (U15)'),
        ('BENJAMIN', 'Benjamin (U13)'),
        ('POUSSIN', 'Poussin (U11)'),
    ]
    
    STATUT_CHOICES = [
        ('ACTIF', 'Actif'),
        ('INACTIF', 'Inactif'),
        ('SUSPENDU', 'Suspendu'),
        ('TRANSFERE', 'Transféré'),
        ('BLESSE', 'Blessé'),
    ]
    
    STATUT_CERTIFICATION_CHOICES = [
        ('PROVISOIRE', 'Provisoire (En attente enrôlement Ligue)'),
        ('EN_ATTENTE_EXAMEN_MEDICAL', 'En attente examen médical (médecin ligue)'),
        ('EN_ATTENTE_VALIDATION_LIGUE', 'Enrôlé (En attente validation Ligue)'),
        ('CERTIFIE_PROVINCIAL', 'Certifié Provincial (En attente validation Fédération)'),
        ('CERTIFIE_NATIONAL', 'Certifié National (Homologué)'),
        ('REJETE_LIGUE', 'Rejeté par la Ligue'),
        ('REJETE_FEDERATION', 'Rejeté par la Fédération'),
    ]
    
    APTITUDE_CHOICES = [
        ('APTE', 'Apte'),
        ('APTE_AVEC_RESERVE', 'Apte avec réserve'),
        ('INAPTE', 'Inapte'),
        ('EN_ATTENTE', 'En attente de visite'),
    ]
    
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # ========== BLOC 1: IDENTITÉ CIVILE (F05, F21) ==========
    # Lien vers Personne pour: Nom, Post-nom, Prénom, Sexe, Date naissance, 
    # Lieu naissance, Nationalité, Photo biométrique
    personne = models.OneToOneField(
        'gouvernance.Personne',
        on_delete=models.CASCADE,
        related_name='athlete',
        null=True,
        blank=True,
        help_text='Informations personnelles de l\'athlète'
    )
    
    # ========== BLOC 2: IDENTIFICATION SPORTIVE (F05, F22) ==========
    # Numéro sportif unique national (généré automatiquement)
    numero_sportif = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        help_text='Numéro sportif unique national (ex: RDC-ATH-2026-001234)'
    )
    
    # Sport / Discipline
    discipline = models.ForeignKey(
        'gouvernance.DisciplineSport',
        on_delete=models.PROTECT,
        related_name='athletes',
        null=True,
        blank=True,
        help_text='Sport/Discipline pratiquée'
    )
    
    # Club actuel
    club = models.ForeignKey(
        'gouvernance.Institution',
        on_delete=models.CASCADE,
        related_name='athletes',
        limit_choices_to={'niveau_territorial': 'CLUB'},
        null=True,
        blank=True,
        help_text='Club d\'appartenance actuel'
    )
    
    # Catégorie d'âge
    categorie = models.CharField(
        max_length=20,
        choices=CATEGORIE_CHOICES,
        blank=True,
        default='SENIOR',
        help_text='Catégorie d\'âge (U17, U20, Senior, etc.)'
    )
    
    # Poste / Position de jeu
    poste = models.CharField(
        max_length=100,
        blank=True,
        help_text='Poste ou spécialité (ex: Gardien, Attaquant, 100m, etc.)'
    )
    
    # Numéro de maillot
    numero_maillot = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(99)],
        help_text='Numéro de maillot (1-99)'
    )
    
    # Date de validité de la licence
    date_validite_licence = models.DateField(
        null=True,
        blank=True,
        help_text='Date de fin de validité de la licence sportive'
    )
    
    # Statut
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='ACTIF',
        help_text='Statut actuel de l\'athlète'
    )
    
    # Statut de certification (workflow de validation)
    statut_certification = models.CharField(
        max_length=35,
        choices=STATUT_CERTIFICATION_CHOICES,
        default='PROVISOIRE',
        help_text='Statut de certification de l\'athlète dans le système'
    )
    
    # ========== ENRÔLEMENT À LA LIGUE ==========
    # Date d'enrôlement à la ligue
    date_enrolement = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Date d\'enrôlement à la ligue provinciale'
    )
    
    # Agent qui a effectué l'enrôlement
    agent_enrolement = models.ForeignKey(
        'core.ProfilUtilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='athletes_enroles',
        help_text='Agent de la ligue qui a effectué l\'enrôlement'
    )
    
    # Certificat médical vérifié lors de l'enrôlement
    certificat_medical_enrolement = models.FileField(
        upload_to='athletes/certificats_enrolement/',
        null=True,
        blank=True,
        help_text='Certificat médical vérifié lors de l\'enrôlement'
    )
    
    # Test médical à la ligue
    date_test_medical = models.DateField(
        null=True,
        blank=True,
        help_text='Date du test médical à la ligue'
    )
    
    resultat_test_medical = models.CharField(
        max_length=20,
        choices=APTITUDE_CHOICES,
        default='EN_ATTENTE',
        help_text='Résultat du test médical'
    )
    
    # Taille et poids (relevés lors du test médical à l'enrôlement)
    taille = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(50), MaxValueValidator(250)],
        help_text='Taille en centimètres (relevée lors du test médical)'
    )
    poids = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(300)],
        help_text='Poids en kilogrammes (relevé lors du test médical)'
    )
    
    # Empreintes digitales
    empreinte_digitale = models.FileField(
        upload_to='athletes/empreintes/',
        null=True,
        blank=True,
        help_text='Fichier des empreintes digitales'
    )
    
    # Observations lors de l'enrôlement
    observations_enrolement = models.TextField(
        blank=True,
        help_text='Observations lors de l\'enrôlement'
    )
    
    # ========== VALIDATION PAR LA LIGUE ==========
    date_validation_ligue = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Date de validation par la Ligue Provinciale'
    )
    
    date_validation_federation = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Date de validation par la Fédération Nationale'
    )
    
    # Validateurs
    validateur_ligue = models.ForeignKey(
        'core.ProfilUtilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='athletes_valides_ligue',
        help_text='Secrétaire de la Ligue qui a validé'
    )
    
    validateur_federation = models.ForeignKey(
        'core.ProfilUtilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='athletes_valides_federation',
        help_text='Secrétaire de la Fédération qui a validé'
    )
    
    # Motifs de rejet
    motif_rejet_ligue = models.TextField(
        blank=True,
        help_text='Motif de rejet par la Ligue'
    )
    
    motif_rejet_federation = models.TextField(
        blank=True,
        help_text='Motif de rejet par la Fédération'
    )
    
    # Date d'inscription dans le club
    date_inscription = models.DateField(
        auto_now_add=True,
        help_text='Date d\'inscription dans le club'
    )
    
    # ========== LICENCE SPORTIVE ==========
    # Numéro de licence (identique au numéro sportif)
    numero_licence = models.CharField(
        max_length=50,
        blank=True,
        help_text='Numéro de licence sportive (identique au numéro sportif)'
    )
    
    # Date d'émission de la licence
    date_emission_licence = models.DateField(
        null=True,
        blank=True,
        help_text='Date d\'émission de la licence'
    )
    
    # Date d'expiration de la licence (1 an après émission)
    date_expiration_licence = models.DateField(
        null=True,
        blank=True,
        help_text='Date d\'expiration de la licence (1 an après émission)'
    )
    
    # Fichier PDF de la licence
    licence_pdf = models.FileField(
        upload_to='licences/',
        null=True,
        blank=True,
        help_text='Fichier PDF de la licence sportive'
    )
    
    # ========== BLOC 3: SANTÉ ET PROTECTION (F05, F29, F32) ==========
    # Groupe sanguin
    groupe_sanguin = models.CharField(
        max_length=5,
        blank=True,
        help_text='Groupe sanguin (A+, B-, O+, AB+, etc.)'
    )
    
    # Allergies connues
    allergies = models.TextField(
        blank=True,
        help_text='Allergies connues (médicaments, aliments, etc.)'
    )
    
    # Certificat médical
    certificat_medical = models.FileField(
        upload_to='athletes/certificats_medicaux/',
        null=True,
        blank=True,
        help_text='Certificat médical d\'aptitude à la pratique sportive'
    )
    
    # Date du certificat médical
    date_certificat_medical = models.DateField(
        null=True,
        blank=True,
        help_text='Date de délivrance du certificat médical'
    )
    
    # Aptitude médicale
    aptitude_medicale = models.CharField(
        max_length=20,
        choices=APTITUDE_CHOICES,
        default='EN_ATTENTE',
        help_text='Aptitude médicale à la pratique sportive'
    )
    
    # Assurance sportive
    assurance_sportive = models.BooleanField(
        default=False,
        help_text='Possède une assurance sportive'
    )
    
    # Numéro de police d'assurance
    numero_assurance = models.CharField(
        max_length=100,
        blank=True,
        help_text='Numéro de police d\'assurance sportive'
    )
    
    # Compagnie d'assurance
    compagnie_assurance = models.CharField(
        max_length=200,
        blank=True,
        help_text='Nom de la compagnie d\'assurance'
    )
    
    # Date d'expiration de l'assurance
    date_expiration_assurance = models.DateField(
        null=True,
        blank=True,
        help_text='Date d\'expiration de l\'assurance sportive'
    )
    
    # ========== CONTACT D'URGENCE ==========
    contact_urgence_nom = models.CharField(
        max_length=200,
        blank=True,
        help_text='Nom complet du contact d\'urgence'
    )
    
    contact_urgence_telephone = models.CharField(
        max_length=20,
        blank=True,
        help_text='Téléphone du contact d\'urgence'
    )
    
    contact_urgence_lien = models.CharField(
        max_length=100,
        blank=True,
        help_text='Lien de parenté (père, mère, tuteur, etc.)'
    )
    
    # ========== MÉTADONNÉES ==========
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    actif = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'athlete'
        verbose_name = 'Athlète'
        verbose_name_plural = 'Athlètes'
        ordering = ['personne__nom', 'personne__prenom']
        unique_together = ['club', 'personne']
    
    def __str__(self):
        if self.personne and self.club:
            return f"{self.personne.nom_complet} - {self.club.nom_officiel}"
        elif self.personne:
            return self.personne.nom_complet
        return f"Athlète {self.uid}"
    
    def save(self, *args, **kwargs):
        """Génère automatiquement le numéro sportif unique si absent."""
        if not self.numero_sportif:
            self.numero_sportif = self.generer_numero_sportif()
        super().save(*args, **kwargs)
    
    def generer_numero_sportif(self):
        """
        Génère un numéro sportif unique national.
        Format: RDC-{DISCIPLINE_CODE}-{ANNEE}-{SEQUENCE}
        Exemple: RDC-FOOT-2026-001234
        """
        from datetime import date
        annee = date.today().year
        
        # Code discipline (4 premiers caractères en majuscules)
        if self.discipline and self.discipline.code:
            discipline_code = self.discipline.code[:4].upper()
        else:
            discipline_code = 'SPOR'
        
        # Compter les athlètes existants pour cette discipline cette année
        if self.discipline:
            count = Athlete.objects.filter(
                discipline=self.discipline,
                date_creation__year=annee
            ).count() + 1
        else:
            count = Athlete.objects.filter(
                discipline__isnull=True,
                date_creation__year=annee
            ).count() + 1
        
        # Générer le numéro
        numero = f"RDC-{discipline_code}-{annee}-{count:06d}"
        
        # Vérifier l'unicité
        while Athlete.objects.filter(numero_sportif=numero).exists():
            count += 1
            numero = f"RDC-{discipline_code}-{annee}-{count:06d}"
        
        return numero
    
    @property
    def nom_complet(self):
        """Retourne le nom complet de l'athlète."""
        if self.personne:
            return self.personne.nom_complet
        return "Athlète sans nom"
    
    @property
    def age(self):
        """Calcule l'âge de l'athlète."""
        if not self.personne or not self.personne.date_naissance:
            return None
        today = date.today()
        return today.year - self.personne.date_naissance.year - (
            (today.month, today.day) < (self.personne.date_naissance.month, self.personne.date_naissance.day)
        )
    
    @property
    def licence_valide(self):
        """Vérifie si la licence est encore valide."""
        if not self.date_validite_licence:
            return False
        return self.date_validite_licence >= date.today()
    
    @property
    def certificat_medical_valide(self):
        """Vérifie si le certificat médical est encore valide (< 1 an)."""
        if not self.date_certificat_medical:
            return False
        from datetime import timedelta
        date_expiration = self.date_certificat_medical + timedelta(days=365)
        return date_expiration >= date.today()

    @property
    def derniere_visite_medicale(self):
        """Dernière visite médicale (F67) enregistrée pour cet athlète."""
        return self.visites_medicales.order_by('-date_visite').first()

    def peut_generer_licence_medical(self):
        """
        Le système ne doit pas autoriser la génération de licence si la dernière visite
        est INAPTE ou si le certificat d'aptitude (F72) n'est pas délivré et joint.
        """
        visite = self.derniere_visite_medicale
        if not visite:
            return False
        return visite.peut_generer_licence()

    @property
    def assurance_valide(self):
        """Vérifie si l'assurance est encore valide."""
        if not self.assurance_sportive or not self.date_expiration_assurance:
            return False
        return self.date_expiration_assurance >= date.today()
