"""
Chef de Division Provinciale - Modèle pour stocker les divisions provinciales.
"""
import uuid
from django.db import models
from django.utils import timezone


class DivisionProvinciale(models.Model):
    """Division Provinciale - Déconcentration de l'État."""
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    province = models.OneToOneField(
        'gouvernance.ProvAdmin',
        on_delete=models.CASCADE,
        related_name='division_provinciale',
        help_text="Province administrative"
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Code unique de la division (ex: DIV-KINSHASA)"
    )
    nom_officiel = models.CharField(
        max_length=255,
        help_text="Nom officiel de la division"
    )
    chef = models.ForeignKey(
        'gouvernance.Agent',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='divisions_chef',
        help_text="Agent assigné comme Chef de Division"
    )
    adresse = models.CharField(
        max_length=500,
        blank=True,
        help_text="Adresse physique de la division"
    )
    telephone = models.CharField(
        max_length=50,
        blank=True,
        help_text="Numéro de téléphone"
    )
    email = models.EmailField(
        blank=True,
        help_text="Email de la division"
    )
    statut = models.CharField(
        max_length=20,
        choices=[
            ('ACTIVE', 'Active'),
            ('INACTIVE', 'Inactive'),
            ('SUSPENDUE', 'Suspendue'),
        ],
        default='ACTIVE',
        help_text="Statut de la division"
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'division_provinciale'
        verbose_name = 'Division Provinciale'
        verbose_name_plural = 'Divisions Provinciales'
        ordering = ['province__designation']

    def __str__(self):
        return f"{self.nom_officiel} ({self.province.designation})"
    
    @property
    def est_assigne(self):
        """Retourne True si un chef est assigné."""
        return self.chef is not None
    
    @property
    def chef_nom_complet(self):
        """Retourne le nom complet du chef s'il existe."""
        return self.chef.personne.nom_complet if self.chef else "Non assigné"

