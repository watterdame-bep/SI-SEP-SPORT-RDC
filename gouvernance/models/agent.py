"""
Agent du Cabinet Ministériel (lié à une Personne).
"""
import uuid
from django.db import models


class Agent(models.Model):
    """Agent du Cabinet Ministériel (Ministre, Conseiller, etc.)."""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    personne = models.OneToOneField(
        'gouvernance.Personne',
        on_delete=models.CASCADE,
        related_name='agent',
        help_text="Identité de la personne"
    )
    institution = models.ForeignKey(
        'gouvernance.Institution',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agents',
        help_text="Institution d'affectation"
    )
    matricule = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        help_text="Matricule unique de l'agent (ex: MIN-2026-001)"
    )
    signature_image = models.ImageField(
        upload_to='agents/signatures/',
        blank=True,
        null=True,
        help_text="Signature scannée de l'agent (PNG avec fond transparent)"
    )
    sceau_image = models.ImageField(
        upload_to='agents/sceaux/',
        blank=True,
        null=True,
        help_text="Sceau officiel (PNG avec fond transparent)"
    )
    date_enregistrement = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'agent'
        verbose_name = 'Agent'
        verbose_name_plural = 'Agents'
        ordering = ['-date_enregistrement']

    def __str__(self):
        return f"{self.personne.nom_complet} ({self.matricule})" if self.matricule else str(self.personne)
    
    @property
    def nom_complet(self):
        """Retourne le nom complet de l'agent."""
        return self.personne.nom_complet
    
    @property
    def email(self):
        """Retourne l'email de l'agent."""
        return self.personne.email
    
    @property
    def telephone(self):
        """Retourne le téléphone de l'agent."""
        return self.personne.telephone
    
    @property
    def photo(self):
        """Retourne la photo de l'agent."""
        return self.personne.photo
