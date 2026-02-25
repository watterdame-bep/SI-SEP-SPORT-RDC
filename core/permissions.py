def peut_acceder_setup_sisep(user):
    """Accès setup réservé au Super Admin Développeur (is_superuser)."""
    return user.is_authenticated and user.is_superuser


def est_secretaire_general_ministere(user):
    """Accès Gestion Administrative : Secrétaire Général lié au Ministère (institution racine)."""
    from .models import RoleUtilisateur
    if not user.is_authenticated:
        return False
    try:
        profil = user.profil_sisep
        return (
            profil.actif
            and profil.role == RoleUtilisateur.INSTITUTION_ADMIN
            and profil.institution_id is not None
            and profil.institution.institution_tutelle_id is None
        )
    except Exception:
        return False


def est_ministre(user):
    """Accès tableau de bord Ministre (validations en attente)."""
    from .models import RoleUtilisateur
    if not user.is_authenticated:
        return False
    try:
        profil = user.profil_sisep
        return profil.actif and profil.role == RoleUtilisateur.MINISTRE
    except Exception:
        return False
