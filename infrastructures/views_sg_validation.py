"""
Vues pour la validation des infrastructures par la SG.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth.models import User
import secrets

from core.permissions import require_role
from .models import Infrastructure


@login_required
@require_role('INSTITUTION_ADMIN', 'MINISTRE')
def infrastructure_validation_list(request):
    """
    Liste des infrastructures en attente de validation pour la SG.
    Avec support pour recherche et filtrage par province et type.
    """
    from django.db.models import Q
    from gouvernance.models import ProvAdmin
    
    infrastructures = Infrastructure.objects.filter(
        statut='EN_ATTENTE'
    ).select_related(
        'type_infrastructure',
        'province_admin'
    ).order_by('-date_creation')
    
    # Recherche par nom ou adresse
    search = request.GET.get('search')
    if search:
        infrastructures = infrastructures.filter(
            Q(nom__icontains=search) | 
            Q(avenue__icontains=search) | 
            Q(quartier__designation__icontains=search)
        )
    
    # Filtrage par province
    province_filter = request.GET.get('province')
    if province_filter:
        infrastructures = infrastructures.filter(province_admin__uid=province_filter)
    
    # Filtrage par type
    type_filter = request.GET.get('type')
    if type_filter:
        infrastructures = infrastructures.filter(type_infrastructure__uid=type_filter)
    
    # Récupérer les options de filtrage
    provinces = ProvAdmin.objects.all().order_by('designation')
    types = Infrastructure.objects.filter(
        statut='EN_ATTENTE'
    ).values_list('type_infrastructure', flat=True).distinct()
    from .models import TypeInfrastructure
    types = TypeInfrastructure.objects.filter(uid__in=types).order_by('designation')
    
    # Stats globales (indépendantes des filtres)
    stats = {
        'en_attente': Infrastructure.objects.filter(statut='EN_ATTENTE').count(),
        'validees': Infrastructure.objects.filter(statut='VALIDEE').count(),
        'rejetees': Infrastructure.objects.filter(statut='REJETEE').count(),
        'total': Infrastructure.objects.filter(actif=True).count(),
    }

    context = {
        'infrastructures': infrastructures,
        'provinces': provinces,
        'types': types,
        'stats': stats,
        'title': 'Infrastructures en attente de validation',
        'user_role': 'sg',
    }
    
    return render(request, 'infrastructures/sg_infrastructure_validation_list.html', context)


@login_required
@require_role('INSTITUTION_ADMIN', 'MINISTRE')
def infrastructure_validation_detail(request, infrastructure_id):
    """
    Détail d'une infrastructure pour validation par la SG.
    """
    infrastructure = get_object_or_404(Infrastructure, uid=infrastructure_id, statut='EN_ATTENTE')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            # Générer le code d'homologation
            code = generate_homologation_code(infrastructure)
            infrastructure.code_homologation = code
            
            # Valider l'infrastructure
            infrastructure.statut = 'VALIDEE'
            infrastructure.save()
            
            # Créer un compte utilisateur pour le gestionnaire
            if infrastructure.email_gestionnaire:
                create_infrastructure_manager_account(infrastructure)
                messages.success(request, f"Infrastructure validée avec le code {code}. Compte créé pour le gestionnaire.")
            else:
                messages.warning(request, f"Infrastructure validée avec le code {code}. Pas d'email pour créer le compte du gestionnaire.")
            
            return redirect('infrastructures:sg_infrastructure_validation_list')
        
        elif action == 'reject':
            motif = request.POST.get('motif_rejet', '')
            infrastructure.statut = 'REJETEE'
            infrastructure.motif_rejet = motif
            infrastructure.save()
            
            messages.success(request, "Infrastructure rejetée")
            return redirect('infrastructures:sg_infrastructure_validation_list')
    
    context = {
        'infrastructure': infrastructure,
        'title': f'Validation: {infrastructure.nom}',
        'user_role': 'sg',
    }
    
    return render(request, 'infrastructures/sg_infrastructure_validation_detail.html', context)


def generate_homologation_code(infrastructure):
    """
    Génère un code d'homologation unique pour l'infrastructure.
    Format: PROV-TYPE-XXX (ex: KIN-STAD-001)
    """
    from gouvernance.models import ProvAdmin
    
    # Obtenir l'abréviation de la province (3 lettres)
    province_code = 'RDC'
    if infrastructure.province_admin:
        # Prendre les 3 premières lettres du nom de la province
        province_code = infrastructure.province_admin.designation[:3].upper()
    
    # Obtenir l'abréviation du type d'infrastructure (4 lettres)
    type_code = 'INFR'
    if infrastructure.type_infrastructure:
        # Prendre les 4 premières lettres du type
        type_code = infrastructure.type_infrastructure.designation[:4].upper()
    
    # Compter les infrastructures validées pour cette province et ce type
    count = Infrastructure.objects.filter(
        province_admin=infrastructure.province_admin,
        type_infrastructure=infrastructure.type_infrastructure,
        statut='VALIDEE'
    ).count() + 1
    
    # Générer le code avec numéro séquentiel (3 chiffres)
    code = f"{province_code}-{type_code}-{count:03d}"
    
    # Vérifier l'unicité
    while Infrastructure.objects.filter(code_homologation=code).exists():
        count += 1
        code = f"{province_code}-{type_code}-{count:03d}"
    
    return code


def create_infrastructure_manager_account(infrastructure):
    """
    Crée un compte utilisateur pour le gestionnaire de l'infrastructure.
    """
    email = infrastructure.email_gestionnaire
    
    # Vérifier si l'utilisateur existe déjà
    if User.objects.filter(email=email).exists():
        return
    
    # Générer un nom d'utilisateur unique
    base_username = f"infra_{infrastructure.code_homologation.lower()}"
    username = base_username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}_{counter}"
        counter += 1
    
    # Générer un mot de passe temporaire
    temp_password = secrets.token_urlsafe(16)
    
    # Créer l'utilisateur
    user = User.objects.create_user(
        username=username,
        email=email,
        first_name=infrastructure.gestionnaire_prenom or '',
        last_name=infrastructure.gestionnaire_nom or '',
        password=temp_password
    )
    
    # Créer le profil utilisateur avec le rôle INFRA_MANAGER
    from core.models import ProfilUtilisateur
    profil = ProfilUtilisateur.objects.create(
        user=user,
        role='INFRA_MANAGER',
        infrastructure=infrastructure
    )
    
    # Générer un token de vérification d'email
    from core.models import EmailVerificationToken
    token = EmailVerificationToken.objects.create(user=user)
    
    # Envoyer l'email de validation
    send_infrastructure_manager_activation_email(user, infrastructure, token)


def send_infrastructure_manager_activation_email(user, infrastructure, token):
    """
    Envoie l'email d'activation au gestionnaire de l'infrastructure.
    """
    verification_url = f"{settings.SITE_URL}/verify-email/{token.token}/"
    
    context = {
        'user': user,
        'infrastructure': infrastructure,
        'infrastructure_nom': infrastructure.nom,
        'code_homologation': infrastructure.code_homologation,
        'province': infrastructure.province_admin.designation if infrastructure.province_admin else 'N/A',
        'type_infrastructure': infrastructure.type_infrastructure.designation if infrastructure.type_infrastructure else 'N/A',
        'gestionnaire_prenom': infrastructure.gestionnaire_prenom,
        'gestionnaire_nom': infrastructure.gestionnaire_nom,
        'verification_url': verification_url,
        'token': token.token,
    }
    
    html_message = render_to_string('emails/infrastructure_manager_activation.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=f"Activation de votre compte - Gestionnaire Infrastructure {infrastructure.nom}",
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )
