"""
Validation des Fédérations par les Chefs de Division Provinciale.
Chaque Chef de Division valide l'existence et l'activité de la fédération dans sa province.
"""
import uuid
from django.db import models
from django.utils import timezone


class ValidationFederation(models.Model):
    """
    Validation d'une fédération par un Chef de Division pour une province donnée.
    """
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente de validation'),
        ('VALIDEE', 'Validée'),
        ('REJETEE', 'Rejetée'),
        ('INCOMPLETE', 'Données incomplètes'),
    ]
    
    CRITERE_CHOICES = [
        ('EXISTENCE', 'Existence physique'),
        ('ACTIVITE', 'Activité réelle'),
        ('CONFORMITE', 'Conformité des dirigeants'),
    ]
    
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Références
    federation = models.ForeignKey(
        'gouvernance.Institution',
        on_delete=models.CASCADE,
        related_name='validations_provinciales',
        help_text="Fédération à valider"
    )
    province = models.ForeignKey(
        'gouvernance.ProvAdmin',
        on_delete=models.CASCADE,
        related_name='validations_federations',
        help_text="Province où la validation est effectuée"
    )
    chef_division = models.ForeignKey(
        'gouvernance.Agent',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validations_effectuees',
        help_text="Chef de Division qui effectue la validation"
    )
    
    # Statut global de la validation
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE',
        db_index=True,
    )
    
    # Critères de validation
    existence_physique = models.BooleanField(
        null=True,
        blank=True,
        help_text="La fédération a-t-elle un bureau/siège dans cette province?"
    )
    activite_reelle = models.BooleanField(
        null=True,
        blank=True,
        help_text="Y a-t-il des athlètes, entraînements et compétitions?"
    )
    conformite_dirigeants = models.BooleanField(
        null=True,
        blank=True,
        help_text="Les dirigeants sont-ils crédibles et connus?"
    )
    
    # Observations et commentaires
    observations = models.TextField(
        blank=True,
        help_text="Observations et commentaires du Chef de Division"
    )
    
    # Dates
    date_creation = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'validation_federation'
        verbose_name = 'Validation Fédération'
        verbose_name_plural = 'Validations Fédérations'
        unique_together = ('federation', 'province')
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.federation.nom_officiel} - {self.province.designation} ({self.statut})"
    
    @property
    def est_validee(self):
        """Retourne True si tous les critères sont validés."""
        return (
            self.existence_physique is True and
            self.activite_reelle is True and
            self.conformite_dirigeants is True
        )
    
    @property
    def est_rejetee(self):
        """Retourne True si au moins un critère est rejeté."""
        return (
            self.existence_physique is False or
            self.activite_reelle is False or
            self.conformite_dirigeants is False
        )
    
    def marquer_comme_validee(self):
        """Marquer la validation comme complète et validée."""
        self.statut = 'VALIDEE'
        self.date_validation = timezone.now()
        self.save()
    
    def marquer_comme_rejetee(self):
        """Marquer la validation comme rejetée."""
        self.statut = 'REJETEE'
        self.date_validation = timezone.now()
        self.save()
