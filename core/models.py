import secrets
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


def _default_token():
    return secrets.token_urlsafe(48)


class RoleUtilisateur(models.TextChoices):
    SYSTEM_SUPER_ADMIN = 'SYSTEM_SUPER_ADMIN', 'Super Admin (Développeur)'
    INSTITUTION_ADMIN = 'INSTITUTION_ADMIN', 'Admin Institution (Secrétaire Général — gestionnaire de données)'
    MINISTRE = 'MINISTRE', 'Ministre'
    DIRECTEUR_CABINET = 'DIRECTEUR_CABINET', 'Directeur de Cabinet'
    DIRECTEUR_PROVINCIAL = 'DIRECTEUR_PROVINCIAL', 'Directeur (Direction provinciale)'
    INSPECTEUR_GENERAL = 'INSPECTEUR_GENERAL', 'Inspection générale'
    FEDERATION_SECRETARY = 'FEDERATION_SECRETARY', 'Secrétaire de Fédération'
    LIGUE_SECRETARY = 'LIGUE_SECRETARY', 'Secrétaire de Ligue Provinciale'
    CLUB_SECRETARY = 'CLUB_SECRETARY', 'Secrétaire de Club'
    INFRA_MANAGER = 'INFRA_MANAGER', 'Gestionnaire d\'Infrastructure'
    MEDECIN_INSPECTEUR = 'MEDECIN_INSPECTEUR', 'Médecin Inspecteur / Validateur'


class ProfilUtilisateur(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profil_sisep',
    )
    agent = models.ForeignKey(
        'gouvernance.Agent',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profils_utilisateur',
        help_text="Agent du cabinet ministériel lié à ce compte"
    )
    personne = models.ForeignKey(
        'gouvernance.Personne',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profils_utilisateur',
        help_text="DEPRECATED: Utiliser 'agent' à la place"
    )
    institution = models.ForeignKey(
        'gouvernance.Institution',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profils_utilisateur',
    )
    # Pour DIRECTEUR_PROVINCIAL : division provinciale (Province administrative) concernée
    province_admin = models.ForeignKey(
        'gouvernance.ProvAdmin',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profils_utilisateur',
    )
    # Pour INFRA_MANAGER : infrastructure gérée
    infrastructure = models.ForeignKey(
        'infrastructures.Infrastructure',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profils_utilisateur',
    )
    role = models.CharField(
        max_length=50,
        choices=RoleUtilisateur.choices,
        default=RoleUtilisateur.INSTITUTION_ADMIN,
    )
    actif = models.BooleanField(default=True)
    # Pour MEDECIN_INSPECTEUR : numéro de l'Ordre des Médecins (obligatoire à la désignation)
    numero_ordre_medecins = models.CharField(
        max_length=50,
        blank=True,
        help_text='Numéro de l\'Ordre des Médecins (pour le Médecin Inspecteur de la Ligue)'
    )
    
    # Signature et Sceau du Ministre (pour les arrêtés)
    signature_image = models.ImageField(
        upload_to='signatures/',
        blank=True,
        null=True,
        help_text="Signature scannée du Ministre (PNG avec fond transparent, 400x200px)"
    )
    sceau_image = models.ImageField(
        upload_to='sceaux/',
        blank=True,
        null=True,
        help_text="Sceau officiel du Ministère (PNG avec fond transparent, 300x300px)"
    )

    class Meta:
        db_table = 'core_profilutilisateur'
        verbose_name = 'Profil utilisateur'
        verbose_name_plural = 'Profils utilisateur'


class EmailVerificationToken(models.Model):
    """Token pour validation par e-mail : activer le compte et définir le mot de passe."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='email_verification_token',
    )
    token = models.CharField(max_length=64, unique=True, default=_default_token, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'core_emailverificationtoken'
        verbose_name = 'Token de vérification e-mail'
        verbose_name_plural = 'Tokens de vérification e-mail'

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at
