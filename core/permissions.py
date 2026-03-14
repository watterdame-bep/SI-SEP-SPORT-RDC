from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden


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


def est_directeur_provincial(user):
    """Accès tableau de bord Directeur Provincial (inspection provinciale)."""
    from .models import RoleUtilisateur
    if not user.is_authenticated:
        return False
    try:
        profil = user.profil_sisep
        return (
            profil.actif
            and profil.role == RoleUtilisateur.DIRECTEUR_PROVINCIAL
            and profil.province_admin_id is not None
        )
    except Exception:
        return False


def est_gestionnaire_infrastructure(user):
    """Accès tableau de bord Gestionnaire d'Infrastructure (gestion opérationnelle du terrain)."""
    from .models import RoleUtilisateur
    if not user.is_authenticated:
        return False
    try:
        profil = user.profil_sisep
        return (
            profil.actif
            and profil.role == RoleUtilisateur.INFRA_MANAGER
            and profil.infrastructure_id is not None
        )
    except Exception:
        return False


def est_secretaire_federation(user):
    """Accès tableau de bord Secrétaire de Fédération (gestion de la fédération)."""
    from .models import RoleUtilisateur
    if not user.is_authenticated:
        return False
    try:
        profil = user.profil_sisep
        return (
            profil.actif
            and profil.role == RoleUtilisateur.FEDERATION_SECRETARY
            and profil.institution_id is not None
        )
    except Exception:
        return False


def est_medecin_inspecteur(user):
    """Médecin Inspecteur / Validateur de la Ligue : gestion des dossiers médicaux des athlètes."""
    from .models import RoleUtilisateur
    if not user.is_authenticated:
        return False
    try:
        profil = user.profil_sisep
        if not profil.actif or profil.role != RoleUtilisateur.MEDECIN_INSPECTEUR:
            return False
        inst = getattr(profil, 'institution', None)
        return inst is not None and getattr(inst, 'niveau_territorial', None) in ('LIGUE', 'LIGUE_PROVINCIALE')
    except Exception:
        return False


def require_role(*roles):
    """Décorateur pour vérifier le rôle de l'utilisateur."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            try:
                from .models import RoleUtilisateur
                profil = request.user.profil_sisep
                if not profil.actif:
                    return HttpResponseForbidden("Votre compte est désactivé.")
                if profil.role in roles:
                    return view_func(request, *args, **kwargs)
                else:
                    # Afficher le rôle actuel et les rôles requis
                    role_display = dict(RoleUtilisateur.choices).get(profil.role, profil.role)
                    required_roles = ', '.join([dict(RoleUtilisateur.choices).get(r, r) for r in roles])
                    return HttpResponseForbidden(f"Accès refusé. Votre rôle: {role_display}. Rôle(s) requis: {required_roles}")
            except Exception as e:
                return HttpResponseForbidden(f"Erreur d'accès: {str(e)}")
        return wrapper
    return decorator
