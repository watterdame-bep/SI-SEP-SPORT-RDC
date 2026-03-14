"""
Model for club validation workflow by provincial directors.
"""
import uuid
from django.db import models
from django.utils import timezone


class ClubValidation(models.Model):
    """
    Tracks the validation of clubs by provincial directors.
    
    Workflow:
    1. Ligue secretary creates a club (status: EN_ATTENTE_VALIDATION)
    2. Provincial director validates physical existence
    3. Ligue secretary affiliates the club (status: AFFILIEE)
    """
    
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('ACCEPTEE', 'Acceptée'),
        ('REJETEE', 'Rejetée'),
        ('AFFILIEE', 'Affiliée'),
    ]
    
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Club being validated
    club = models.OneToOneField(
        'Institution',
        on_delete=models.CASCADE,
        related_name='validation_club',
        help_text='Club à valider'
    )
    
    # Provincial division responsible for validation
    division_provinciale = models.ForeignKey(
        'Institution',
        on_delete=models.CASCADE,
        related_name='validations_clubs',
        help_text='Direction provinciale responsable de la validation'
    )
    
    # Validation details
    date_demande = models.DateTimeField(
        auto_now_add=True,
        help_text='Date de création de la demande'
    )
    
    date_validation = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Date de validation par la direction provinciale'
    )
    
    # Physical existence confirmation
    existence_physique_confirmee = models.BooleanField(
        default=False,
        help_text='Existence physique confirmée'
    )
    
    # Validation status
    statut = models.CharField(
        max_length=50,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE',
        db_index=True
    )
    
    # Rejection reason (if applicable)
    motif_rejet = models.TextField(
        blank=True,
        help_text='Motif du rejet (si applicable)'
    )
    
    # Who validated
    validee_par = models.ForeignKey(
        'core.ProfilUtilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clubs_valides',
        help_text='Utilisateur qui a validé'
    )
    
    class Meta:
        db_table = 'club_validation'
        verbose_name = 'Validation de club'
        verbose_name_plural = 'Validations de clubs'
        ordering = ['-date_demande']
    
    def __str__(self):
        return f"Validation - {self.club.nom_officiel} ({self.get_statut_display()})"
    
    def accepter(self, user):
        """Accept the club validation."""
        self.statut = 'ACCEPTEE'
        self.date_validation = timezone.now()
        self.validee_par = user
        self.save()
        
        # Update club status
        self.club.statut_validation_club = 'VALIDEE_PROVINCIALE'
        self.club.existence_physique_confirmee = self.existence_physique_confirmee
        self.club.save()
    
    def rejeter(self, user, motif):
        """Reject the club validation."""
        self.statut = 'REJETEE'
        self.date_validation = timezone.now()
        self.validee_par = user
        self.motif_rejet = motif
        self.save()
        
        # Update club status
        self.club.statut_validation_club = 'REJETEE_PROVINCIALE'
        self.club.save()
