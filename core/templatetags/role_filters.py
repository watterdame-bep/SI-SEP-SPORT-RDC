from django import template

register = template.Library()

ROLE_LABELS_COURTS = {
    'SYSTEM_SUPER_ADMIN': 'Super Admin',
    'MINISTRE': 'Ministre',
    'INSTITUTION_ADMIN': 'Secrétaire Général',
    'INSTITUTION_AGENT': 'Agent',
    'DIRECTEUR_PROVINCIAL': 'Directeur Provincial',
    'FEDERATION_SECRETARY': 'Secrétaire',
    'CLUB_SECRETARY': 'Secrétaire Club',
    'MEDECIN_INSPECTEUR': 'Médecin',
    'INFRA_MANAGER': 'Gestionnaire Infra',
}


@register.filter
def role_court(profil):
    """Retourne le label court du rôle d'un ProfilUtilisateur."""
    if not profil:
        return ''
    role = getattr(profil, 'role', None)
    if not role:
        return ''
    return ROLE_LABELS_COURTS.get(str(role), profil.get_role_display())
