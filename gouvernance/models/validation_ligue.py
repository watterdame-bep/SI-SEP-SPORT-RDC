"""
Validation des Ligues Provinciales par les Chefs de Division et le Secrétaire Général.
Workflow: Division Provinciale → Secrétaire Général → Attestation de Reconnaissance
"""
import uuid
from django.db import models
from django.utils import timezone


class ValidationLigue(models.Model):
    """
    Validation d'une ligue provinciale par le Chef de Division.
    Workflow bidirectionnel: SG ↔ Division Provinciale
    """
    STATUT_CHOICES = [
        ('EN_ATTENTE_SG', 'En attente - SG doit transférer'),
        ('EN_INSPECTION', 'En inspection - Division Provinciale'),
        ('INSPECTION_VALIDEE', 'Inspection validée - Retour au SG'),
        ('INSPECTION_REJETEE', 'Inspection rejetée - Retour au SG'),
        ('VALIDEE', 'Validée par la Division'),
        ('REJETEE', 'Rejetée par la Division'),
        ('INCOMPLETE', 'Données incomplètes'),
    ]
    
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Références
    ligue = models.ForeignKey(
        'gouvernance.Institution',
        on_delete=models.CASCADE,
        related_name='validations_division',
        limit_choices_to={'niveau_territorial': 'LIGUE'},
        help_text="Ligue provinciale à valider"
    )
    division_provinciale = models.ForeignKey(
        'gouvernance.DivisionProvinciale',
        on_delete=models.CASCADE,
        related_name='validations_ligues_effectuees',
        null=True,
        blank=True,
        help_text="Division Provinciale qui effectue la validation"
    )
    chef_division = models.ForeignKey(
        'gouvernance.Agent',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validations_ligues_effectuees',
        help_text="Chef de Division qui effectue la validation"
    )
    
    # Statut de la validation
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE_SG',
        db_index=True,
    )
    
    # Transfert à la Division Provinciale
    date_transfert_division = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date du transfert à la Division Provinciale"
    )
    transfert_par = models.ForeignKey(
        'core.ProfilUtilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transferts_ligues_effectues',
        help_text="SG qui a transféré le dossier"
    )
    
    # Critères de validation - Anciens critères
    clubs_existent = models.BooleanField(
        null=True,
        blank=True,
        help_text="Les clubs affiliés existent-ils réellement dans la province?"
    )
    structure_valide = models.BooleanField(
        null=True,
        blank=True,
        help_text="La structure de la ligue est-elle valide?"
    )
    dirigeants_credibles = models.BooleanField(
        null=True,
        blank=True,
        help_text="Les dirigeants sont-ils crédibles et connus?"
    )
    
    # Critères de validation - Nouveaux critères détaillés
    conformite_mandat = models.BooleanField(
        null=True,
        blank=True,
        help_text="Conformité du Mandat : Les délégués provinciaux sont-ils reconnus par la Fédération Nationale ?"
    )
    siege_social_provincial = models.BooleanField(
        null=True,
        blank=True,
        help_text="Siège Social Provincial : L'adresse physique dans la province est-elle vérifiée et fonctionnelle ?"
    )
    existence_clubs = models.BooleanField(
        null=True,
        blank=True,
        help_text="Existence des Clubs : La ligue dispose-t-elle du nombre minimum de clubs actifs requis ?"
    )
    
    # Observations et commentaires
    observations = models.TextField(
        blank=True,
        help_text="Observations et commentaires du Chef de Division"
    )
    
    # Rapport d'inspection
    rapport_inspection = models.FileField(
        upload_to='institutions/rapports_inspection/',
        blank=True,
        null=True,
        max_length=500,
        help_text="Rapport d'inspection provinciale signé"
    )
    
    # Dates
    date_creation = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'validation_ligue'
        verbose_name = 'Validation Ligue'
        verbose_name_plural = 'Validations Ligues'
        unique_together = ('ligue', 'division_provinciale')
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.ligue.nom_officiel} - {self.division_provinciale.nom_officiel} ({self.statut})"
    
    @property
    def est_validee(self):
        """Retourne True si tous les critères sont validés."""
        return (
            self.clubs_existent is True and
            self.structure_valide is True and
            self.dirigeants_credibles is True
        )
    
    @property
    def est_rejetee(self):
        """Retourne True si au moins un critère est rejeté."""
        return (
            self.clubs_existent is False or
            self.structure_valide is False or
            self.dirigeants_credibles is False
        )
    
    def marquer_comme_validee(self):
        """Marquer la validation comme complète et validée."""
        self.statut = 'VALIDEE'
        self.date_validation = timezone.now()
        self.save()
        
        # Mettre à jour le statut d'inspection de la ligue
        self.ligue.statut_inspection = 'INSPECTION_VALIDEE'
        self.ligue.save()
    
    def marquer_comme_rejetee(self):
        """Marquer la validation comme rejetée."""
        self.statut = 'REJETEE'
        self.date_validation = timezone.now()
        self.save()
        
        # Mettre à jour le statut d'inspection de la ligue
        self.ligue.statut_inspection = 'INSPECTION_REJETEE'
        self.ligue.save()
    
    def transferer_a_division(self, utilisateur):
        """Transférer le dossier à la Division Provinciale (SG)."""
        self.statut = 'EN_INSPECTION'
        self.date_transfert_division = timezone.now()
        self.transfert_par = utilisateur
        self.save()
        
        # Mettre à jour le statut d'inspection de la ligue
        self.ligue.statut_inspection = 'EN_INSPECTION'
        self.ligue.save()
    
    def retourner_au_sg(self):
        """Retourner le dossier au SG après inspection."""
        if self.statut == 'EN_INSPECTION':
            # Le statut sera mis à jour par la Division (INSPECTION_VALIDEE ou INSPECTION_REJETEE)
            pass


class AttestationReconnaissance(models.Model):
    """
    Attestation de Reconnaissance délivrée par le Secrétaire Général.
    Étape 2 du workflow de validation (après validation de la Division).
    """
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente de validation SG'),
        ('APPROUVEE', 'Approuvée par le SG'),
        ('REJETEE', 'Rejetée par le SG'),
    ]
    
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Références
    ligue = models.ForeignKey(
        'gouvernance.Institution',
        on_delete=models.CASCADE,
        related_name='attestations_reconnaissance',
        limit_choices_to={'niveau_territorial': 'LIGUE'},
        help_text="Ligue provinciale"
    )
    validation_division = models.OneToOneField(
        'ValidationLigue',
        on_delete=models.CASCADE,
        related_name='attestation',
        help_text="Validation de la Division Provinciale"
    )
    
    # Statut
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE',
        db_index=True,
    )
    
    # Numéro d'attestation
    numero_attestation = models.CharField(
        max_length=100,
        blank=True,
        unique=True,
        help_text="Numéro d'attestation (ex: RDC/MIN-SPORT/LIGUE/2026-001)"
    )
    
    # Document d'attestation
    document_attestation = models.FileField(
        upload_to='institutions/attestations/',
        blank=True,
        null=True,
        max_length=500,
        help_text="Attestation de Reconnaissance (PDF)"
    )
    
    # Observations du SG
    observations_sg = models.TextField(
        blank=True,
        help_text="Observations et commentaires du Secrétaire Général"
    )
    
    # Dates
    date_creation = models.DateTimeField(auto_now_add=True)
    date_approbation = models.DateTimeField(null=True, blank=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'attestation_reconnaissance'
        verbose_name = 'Attestation de Reconnaissance'
        verbose_name_plural = 'Attestations de Reconnaissance'
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"Attestation - {self.ligue.nom_officiel} ({self.statut})"
    
    def approuver(self, numero_attestation):
        """Approuver l'attestation et générer le numéro."""
        self.statut = 'APPROUVEE'
        self.numero_attestation = numero_attestation
        self.date_approbation = timezone.now()
        self.save()
        
        # Mettre à jour le statut de la ligue
        self.ligue.statut_signature = 'SIGNE'
        self.ligue.numero_homologation = numero_attestation
        self.ligue.date_generation_certificat = timezone.now()
        self.ligue.statut_activation = 'ACTIVE'  # Ligue becomes ACTIVE when fully validated
        self.ligue.save()
    
    def rejeter(self):
        """Rejeter l'attestation."""
        self.statut = 'REJETEE'
        self.date_approbation = timezone.now()
        self.save()
        
        # Mettre à jour le statut de la ligue
        self.ligue.statut_signature = 'REFUSE'
        self.ligue.save()
