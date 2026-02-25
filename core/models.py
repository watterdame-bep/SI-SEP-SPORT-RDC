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


class ProfilUtilisateur(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profil_sisep',
    )
    personne = models.ForeignKey(
        'gouvernance.Personne',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profils_utilisateur',
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
    role = models.CharField(
        max_length=50,
        choices=RoleUtilisateur.choices,
        default=RoleUtilisateur.INSTITUTION_ADMIN,
    )
    actif = models.BooleanField(default=True)

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
