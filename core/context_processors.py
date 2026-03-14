"""Context processors pour exposer le rôle utilisateur aux templates."""
from .models import RoleUtilisateur


def user_role(request):
    """
    Ajoute user_role au contexte basé sur le rôle et l'institution de l'utilisateur.
    Valeurs possibles: 'ministre' | 'sg' | 'directeur_provincial' | 'ligue_secretary' | 'federation_secretary' | 'club_secretary' | 'infra_manager' | 'superadmin' | None
    """
    if not request.user.is_authenticated:
        return {'user_role': None}
    
    try:
        profil = request.user.profil_sisep
        role = profil.role
        
        # Super Admin
        if role == RoleUtilisateur.SYSTEM_SUPER_ADMIN:
            return {'user_role': 'superadmin'}
        
        # Ministre
        if role == RoleUtilisateur.MINISTRE:
            return {'user_role': 'ministre'}
        
        # Secrétaire Général (Admin Institution au niveau du Ministère)
        if role == RoleUtilisateur.INSTITUTION_ADMIN:
            inst = getattr(profil, 'institution', None)
            if inst and getattr(inst, 'institution_tutelle_id', None) is None:
                return {'user_role': 'sg'}
        
        # Directeur Provincial
        if role == RoleUtilisateur.DIRECTEUR_PROVINCIAL:
            if getattr(profil, 'province_admin_id', None) is not None:
                return {'user_role': 'directeur_provincial'}
        
        # Secrétaire de Fédération ou Ligue
        if role == RoleUtilisateur.FEDERATION_SECRETARY:
            inst = getattr(profil, 'institution', None)
            if inst:
                # Ligue Provinciale
                if getattr(inst, 'niveau_territorial', None) == 'LIGUE':
                    return {'user_role': 'ligue_secretary'}
                # Fédération Nationale
                elif getattr(inst, 'niveau_territorial', None) == 'FEDERATION':
                    return {'user_role': 'federation_secretary'}
        
        # Secrétaire de Club
        if role == RoleUtilisateur.CLUB_SECRETARY:
            inst = getattr(profil, 'institution', None)
            if inst and getattr(inst, 'niveau_territorial', None) == 'CLUB':
                return {'user_role': 'club_secretary'}
        
        # Gestionnaire d'Infrastructure
        if role == RoleUtilisateur.INFRA_MANAGER:
            if getattr(profil, 'infrastructure_id', None) is not None:
                return {'user_role': 'infra_manager'}
        
        # Médecin Inspecteur / Validateur (médecin de la Ligue provinciale)
        if role == RoleUtilisateur.MEDECIN_INSPECTEUR:
            inst = getattr(profil, 'institution', None)
            if inst and getattr(inst, 'niveau_territorial', None) in ('LIGUE', 'LIGUE_PROVINCIALE'):
                return {'user_role': 'medecin_inspecteur'}
    
    except Exception:
        pass
    
    return {'user_role': None}


def athletes_counts(request):
    """
    Ajoute les compteurs d'athlètes en attente de validation au contexte.
    """
    if not request.user.is_authenticated:
        return {}
    
    try:
        profil = request.user.profil_sisep
        role = profil.role
        
        # Pour le secrétaire de la Ligue (FEDERATION_SECRETARY avec institution de type LIGUE)
        if role == RoleUtilisateur.FEDERATION_SECRETARY:
            inst = getattr(profil, 'institution', None)
            niveau = getattr(inst, 'niveau_territorial', None) if inst else None
            if inst and niveau in ['LIGUE', 'LIGUE_PROVINCIALE']:
                from gouvernance.models import Athlete, Institution
                
                # Compter les athlètes PROVISOIRES (en attente d'enrôlement)
                clubs_province = Institution.objects.filter(
                    niveau_territorial='CLUB',
                    institution_tutelle=inst
                )
                enrollment_count = Athlete.objects.filter(
                    club__in=clubs_province,
                    statut_certification='PROVISOIRE',
                    actif=True
                ).count()
                
                # Compter les athlètes EN_ATTENTE_VALIDATION_LIGUE (enrôlés, en attente de validation)
                validation_count = Athlete.objects.filter(
                    club__in=clubs_province,
                    statut_certification='EN_ATTENTE_VALIDATION_LIGUE',
                    actif=True
                ).count()
                
                # Compter les athlètes ayant réussi leur certification (provinciale ou nationale)
                certifies_count = Athlete.objects.filter(
                    club__in=clubs_province,
                    statut_certification__in=('CERTIFIE_PROVINCIAL', 'CERTIFIE_NATIONAL'),
                    actif=True
                ).count()
                
                return {
                    'athletes_enrollment_count': enrollment_count,
                    'athletes_validation_count': validation_count,
                    'athletes_certifies_count': certifies_count,
                }
        
        # Pour le secrétaire de la Fédération nationale (FEDERATION_SECRETARY avec institution de type FEDERATION)
        if role == RoleUtilisateur.FEDERATION_SECRETARY:
            inst = getattr(profil, 'institution', None)
            niveau = getattr(inst, 'niveau_territorial', None) if inst else None
            if inst and niveau == 'FEDERATION':
                from gouvernance.models import Athlete
                # Compter les athlètes CERTIFIE_PROVINCIAL pour cette discipline
                count = Athlete.objects.filter(
                    discipline__in=inst.disciplines.all(),
                    statut_certification='CERTIFIE_PROVINCIAL',
                    actif=True
                ).count()
                return {'athletes_certification_count': count}
    
    except Exception:
        pass
    
    return {}
