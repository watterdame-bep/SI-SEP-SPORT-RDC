"""Context processors pour exposer le rôle utilisateur aux templates."""
from .models import RoleUtilisateur


def user_role(request):
    """Ajoute user_role ('ministre' | 'sg' | 'superadmin' | None) au contexte."""
    if not request.user.is_authenticated:
        return {'user_role': None}
    try:
        role = request.user.profil_sisep.role
        if role == RoleUtilisateur.MINISTRE:
            return {'user_role': 'ministre'}
        if role == RoleUtilisateur.INSTITUTION_ADMIN:
            inst = getattr(request.user.profil_sisep, 'institution', None)
            if inst and getattr(inst, 'institution_tutelle_id', None) is None:
                return {'user_role': 'sg'}
        if role == RoleUtilisateur.SYSTEM_SUPER_ADMIN:
            return {'user_role': 'superadmin'}
    except Exception:
        pass
    return {'user_role': None}
