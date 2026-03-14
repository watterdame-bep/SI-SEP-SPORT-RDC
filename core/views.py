from datetime import date, timedelta
import secrets
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.files.base import ContentFile
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from gouvernance.models import (
    TypeInstitution,
    Institution,
    Fonction,
    Personne,
    Membre,
    Mandat,
    AdresseContact,
    EtatAdministrative,
    EtatAgrement,
    ProvAdmin,
    DisciplineSport,
)
from .models import ProfilUtilisateur, RoleUtilisateur, EmailVerificationToken
from .permissions import peut_acceder_setup_sisep, est_secretaire_general_ministere, est_ministre
from .forms import (
    SetupInitialForm,
    SetPasswordVerificationForm,
    FederationRegistrationForm,
    CreerCompteEntiteForm,
    DisciplineSportForm,
)

User = get_user_model()

CODE_MINISTERE = 'MIN-SPORTS'


def _envoyer_email_verification(user, request, role_label):
    """Crée un token de vérification, envoie l'e-mail avec le lien d'activation."""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting email verification for user: {user.email}")
    
    token_obj = EmailVerificationToken.objects.create(
        user=user,
        expires_at=timezone.now() + timedelta(days=7),
    )
    verification_url = request.build_absolute_uri(
        reverse('core:verify_email', kwargs={'token': token_obj.token})
    )
    context = {'verification_url': verification_url, 'role_label': role_label}
    subject = 'Activez votre compte SI-SEP Sport RDC'
    text_body = render_to_string('core/email_verification_body.txt', context)
    html_body = render_to_string('core/email_verification_body.html', context)
    
    logger.debug(f"Email subject: {subject}")
    logger.debug(f"Email recipient: {user.email}")
    logger.debug(f"Verification URL: {verification_url}")
    
    email = EmailMultiAlternatives(
        subject,
        text_body,
        getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@sisep-sport.gouv.cd'),
        [user.email],
    )
    email.attach_alternative(html_body, 'text/html')
    
    logger.info(f"Sending email to {user.email}")
    result = email.send(fail_silently=False)
    logger.info(f"Email sent successfully. Result: {result}")


def _user_passes_test(test_func, login_url=None):
    from django.contrib.auth.views import redirect_to_login
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            return redirect_to_login(request.get_full_path(), login_url=login_url)
        return wrapper
    return decorator


class CustomLoginView(LoginView):
    template_name = 'core/login.html'
    # Désactivé pour éviter la boucle : /login/ → / → dashboard → /login/ (cookies/session incohérents)
    redirect_authenticated_user = False

    def get(self, request, *args, **kwargs):
        """Si déjà connecté, afficher une page avec lien vers l'accueil (pas de 302 pour éviter la boucle)."""
        if request.user.is_authenticated:
            return render(request, 'core/already_logged_in.html', {})
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        next_url = self.get_redirect_url()
        if next_url:
            return next_url
        try:
            profil = self.request.user.profil_sisep
            if profil.actif and profil.role == RoleUtilisateur.SYSTEM_SUPER_ADMIN:
                return reverse('core:setup_sisep')
            if profil.actif and profil.role == RoleUtilisateur.INSTITUTION_ADMIN and profil.institution_id and getattr(profil.institution, 'institution_tutelle_id', None) is None:
                return reverse('gouvernance:sg_dashboard')
            if profil.actif and profil.role == RoleUtilisateur.MINISTRE:
                return reverse('gouvernance:minister_dashboard')
            if profil.actif and profil.role == RoleUtilisateur.DIRECTEUR_PROVINCIAL:
                return reverse('gouvernance:directeur_provincial_dashboard')
            if profil.actif and profil.role == RoleUtilisateur.MEDECIN_INSPECTEUR:
                return reverse('gouvernance:medecin_dashboard')
            if profil.actif and profil.role == RoleUtilisateur.FEDERATION_SECRETARY:
                # Différencier entre secrétaire de fédération et secrétaire de ligue
                if profil.institution and profil.institution.niveau_territorial == 'LIGUE':
                    return reverse('gouvernance:ligue_secretary_dashboard')
                else:
                    return reverse('gouvernance:federation_secretary_dashboard')
            if profil.actif and profil.role == RoleUtilisateur.CLUB_SECRETARY:
                return reverse('gouvernance:club_secretary_dashboard')
        except ProfilUtilisateur.DoesNotExist:
            pass
        return reverse('core:home')
    
    def form_invalid(self, form):
        """Personnaliser le message d'erreur de connexion."""
        # Remplacer tous les messages d'erreur par un message simple
        form.errors.clear()
        form.add_error(None, "Nom d'utilisateur ou mot de passe incorrect.")
        return super().form_invalid(form)


def home(request):
    if not request.user.is_authenticated:
        # Éviter la boucle de redirection (/) → (/login/) → (/) en renvoyant une page
        # au lieu d’une redirection 302, surtout si les cookies sont refusés ou mal pris en compte.
        return render(request, 'core/redirect_to_login.html', {})
    try:
        profil = request.user.profil_sisep
        if profil.actif and profil.role == RoleUtilisateur.SYSTEM_SUPER_ADMIN:
            return redirect('core:setup_sisep')
        if profil.actif and profil.role == RoleUtilisateur.INSTITUTION_ADMIN and profil.institution_id and getattr(profil.institution, 'institution_tutelle_id', None) is None:
            return redirect('gouvernance:sg_dashboard')
        if profil.actif and profil.role == RoleUtilisateur.MINISTRE:
            return redirect('gouvernance:minister_dashboard')
        if profil.actif and profil.role == RoleUtilisateur.DIRECTEUR_PROVINCIAL:
            return redirect('gouvernance:directeur_provincial_dashboard')
        if profil.actif and profil.role == RoleUtilisateur.MEDECIN_INSPECTEUR:
            return redirect('gouvernance:medecin_dashboard')
        if profil.actif and profil.role == RoleUtilisateur.FEDERATION_SECRETARY:
            # Différencier entre secrétaire de fédération et secrétaire de ligue
            if profil.institution and profil.institution.niveau_territorial == 'LIGUE':
                return redirect('gouvernance:ligue_secretary_dashboard')
            else:
                return redirect('gouvernance:federation_secretary_dashboard')
        if profil.actif and profil.role == RoleUtilisateur.CLUB_SECRETARY:
            return redirect('gouvernance:club_secretary_dashboard')
        if profil.actif and profil.role == RoleUtilisateur.INFRA_MANAGER:
            return redirect('infrastructures:infra_manager_dashboard')
    except ProfilUtilisateur.DoesNotExist:
        pass
    return render(request, 'core/home.html', {})


@login_required(login_url='/login/')
@_user_passes_test(peut_acceder_setup_sisep, login_url='/login/')
def setup_sisep(request):
    """
    Page « Initialisation du Système » : formulaire Ministère + trois comptes clés.
    Réservée au SYSTEM_SUPER_ADMIN. Génère des mots de passe temporaires et les affiche.
    """
    institution_racine = Institution.objects.filter(institution_tutelle__isnull=True).first()

    if institution_racine:
        return render(request, 'core/setup_sisep.html', {
            'institution_racine': institution_racine,
            'setup_deja_fait': True,
        })

    if request.method == 'POST':
        form = SetupInitialForm(request.POST, request.FILES)
        if form.is_valid():
            cd = form.cleaned_data
            try:
                with transaction.atomic():
                    type_min, _ = TypeInstitution.objects.get_or_create(
                        code='MINISTERE', defaults={'designation': 'Ministère'},
                    )
                    inst = Institution(
                        code=CODE_MINISTERE,
                        nom_officiel=cd['nom_officiel'],
                        sigle=cd.get('sigle') or '',
                        type_institution=type_min,
                        institution_tutelle=None,
                        niveau_territorial='NATIONAL',
                        statut_juridique='Public',
                        email_officiel=cd.get('email_officiel') or '',
                        telephone_off=cd.get('telephone_off') or '',
                        statut_activation='ACTIVE',
                        statut_validee=True,
                    )
                    if cd.get('logo'):
                        inst.logo = cd['logo']
                    inst.save()

                    if cd.get('adresse'):
                        AdresseContact.objects.create(
                            institution=inst,
                            avenue=cd['adresse'][:255],
                        )

                    def _creer_compte_avec_validation_email(role_label, nom_complet, email, role_sisep=None, is_staff=False):
                        parts = (nom_complet or '').strip().split(None, 1)
                        prenom = parts[1] if len(parts) > 1 else ''
                        nom = parts[0] if parts else email.split('@')[0]
                        personne = Personne.objects.create(
                            nom=nom, postnom='', prenom=prenom, email=email,
                        )
                        fct, _ = Fonction.objects.get_or_create(
                            designation=role_label, defaults={'ordre_priorite': 0},
                        )
                        membre = Membre.objects.create(
                            personne=personne, institution=inst, fonction=fct,
                        )
                        Mandat.objects.create(
                            membre=membre, date_debut=date.today(), statut_mandat='En cours',
                        )
                        username = email
                        if User.objects.filter(username=username).exists():
                            username = f"{email.split('@')[0]}_{role_label[:3].upper()}"
                        user = User.objects.create_user(
                            username=username,
                            email=email,
                            first_name=prenom or nom,
                            last_name=nom,
                            password=secrets.token_urlsafe(32),  # remplacé après validation e-mail
                            is_staff=is_staff,
                            is_active=False,
                            is_superuser=False,
                        )
                        if role_sisep is not None:
                            ProfilUtilisateur.objects.create(
                                user=user,
                                personne=personne,
                                institution=inst,
                                role=role_sisep,
                                actif=True,
                            )
                        _envoyer_email_verification(user, request, role_label)
                        return {'email': email, 'role_label': role_label}

                    comptes_crees = {
                        'ministre': _creer_compte_avec_validation_email(
                            'Ministre', cd['ministre_nom'], cd['ministre_email'],
                            role_sisep=RoleUtilisateur.MINISTRE,
                        ),
                        'sg': _creer_compte_avec_validation_email(
                            'Secrétaire Général', cd['sg_nom'], cd['sg_email'],
                            role_sisep=RoleUtilisateur.INSTITUTION_ADMIN,
                            is_staff=True,
                        ),
                    }
                    return render(request, 'core/setup_sisep.html', {
                        'institution_racine': inst,
                        'setup_success': True,
                        'comptes_crees': comptes_crees,
                    })
            except Exception as e:
                messages.error(request, f"Erreur : {e}")
        else:
            messages.error(request, "Veuillez corriger les erreurs du formulaire.")
    else:
        form = SetupInitialForm()

    return render(request, 'core/setup_sisep.html', {
        'institution_racine': None,
        'form': form,
        'setup_deja_fait': False,
    })


@require_http_methods(['GET', 'POST'])
def verify_email(request, token):
    """
    Page de validation par e-mail : l'utilisateur clique sur le lien reçu,
    définit son mot de passe, puis son compte est activé.
    """
    token_obj = EmailVerificationToken.objects.filter(token=token).select_related('user').first()
    if not token_obj:
        return render(request, 'core/verify_email.html', {'valid': False, 'error': 'Lien invalide ou déjà utilisé.'})
    if token_obj.is_expired:
        return render(request, 'core/verify_email.html', {'valid': False, 'error': 'Ce lien a expiré.'})

    if request.method == 'POST':
        form = SetPasswordVerificationForm(request.POST)
        if form.is_valid():
            user = token_obj.user
            user.set_password(form.cleaned_data['password'])
            user.is_active = True
            user.save()
            token_obj.delete()
            messages.success(request, 'Votre compte est activé. Connectez-vous avec votre e-mail et le mot de passe choisi.')
            return redirect('core:login')
    else:
        form = SetPasswordVerificationForm()

    return render(request, 'core/verify_email.html', {
        'valid': True,
        'form': form,
        'email': token_obj.user.email,
    })


def _get_ministere_racine():
    """Retourne l'institution Ministère (racine)."""
    return Institution.objects.filter(institution_tutelle__isnull=True).first()


def _gen_code_federation(sigle):
    """Génère un code unique pour une fédération à partir du sigle."""
    base = f"FED-{(sigle or 'X').upper().replace(' ', '')[:20]}"
    code = base
    n = 0
    while Institution.objects.filter(code=code).exists():
        n += 1
        code = f"{base}-{n}"
    return code


@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
def gestion_administrative(request):
    """
    Vue « Gestion Administrative » pour le Secrétaire Général.
    Bouton « Enregistrer une Fédération » ouvre le formulaire F03.
    Soumission : institution créée avec statut ATTENTE_SIGNATURE (visible chez le Ministre).
    """
    ministere = _get_ministere_racine()
    if not ministere:
        messages.error(request, "Aucun ministère trouvé. Effectuez d'abord l'initialisation du système.")
        return redirect('core:home')

    # Fédérations en attente (créées par ce SG)
    en_attente = Institution.objects.filter(
        institution_tutelle=ministere,
        statut_signature='ATTENTE_SIGNATURE',
    ).order_by('-nom_officiel')

    if request.method == 'POST' and request.POST.get('form_type') == 'f03':
        form = FederationRegistrationForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            type_fed, _ = TypeInstitution.objects.get_or_create(
                code='FEDERATION',
                defaults={'designation': 'Fédération'},
            )
            code = _gen_code_federation(cd['sigle'])
            with transaction.atomic():
                inst = Institution(
                    code=code,
                    nom_officiel=cd['nom_officiel'],
                    sigle=cd.get('sigle') or '',
                    type_institution=type_fed,
                    institution_tutelle=ministere,
                    niveau_territorial='FEDERATION',
                    statut_juridique=cd.get('statut_juridique') or '',
                    date_creation=cd.get('date_creation'),
                    email_officiel=cd.get('email_officiel') or '',
                    telephone_off=cd.get('telephone_off') or '',
                    statut_activation='INACTIF',
                    statut_validee=False,
                    statut_signature='ATTENTE_SIGNATURE',
                )
                inst.save()
                if cd.get('siege'):
                    AdresseContact.objects.create(
                        institution=inst,
                        avenue=cd['siege'][:255],
                    )
            messages.success(request, f"Fédération « {inst.nom_officiel} » enregistrée. En attente de signature du Ministre.")
            return redirect('core:gestion_administrative')
    else:
        form = FederationRegistrationForm()

    return render(request, 'core/gestion_administrative.html', {
        'ministere': ministere,
        'form': form,
        'en_attente': en_attente,
        'user_role': 'sg',
    })


@login_required(login_url='/login/')
def gerer_comptes(request):
    """
    Page unique « Gérer comptes » en LECTURE SEULE.
    Affiche uniquement les comptes de l'entité de l'utilisateur (isolation stricte).
    - SG (Ministère) : Voit les comptes du ministère
    - Admin Fédération : Voit uniquement les comptes de SA fédération
    - Admin Direction provinciale : Voit uniquement les comptes de SA direction
    """
    try:
        profil = request.user.profil_sisep
    except ProfilUtilisateur.DoesNotExist:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    if not profil.institution:
        messages.error(request, "Aucune institution associée à votre profil.")
        return redirect('core:home')
    
    mon_institution = profil.institution
    
    # Récupérer tous les utilisateurs de MON institution uniquement (isolation stricte)
    comptes_mon_entite = ProfilUtilisateur.objects.filter(
        institution=mon_institution
    ).select_related('user', 'personne', 'province_admin').order_by('-user__date_joined')
    
    return render(request, 'core/gerer_comptes.html', {
        'mon_institution': mon_institution,
        'comptes_mon_entite': comptes_mon_entite,
        'user_role': 'sg',
    })





@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
def parametres_fonctions(request):
    """
    Page de paramètres pour gérer les fonctions du ministère.
    Accessible uniquement au Secrétaire Général.
    """
    from gouvernance.models import Fonction
    
    try:
        profil = request.user.profil_sisep
    except ProfilUtilisateur.DoesNotExist:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    if not profil.institution:
        messages.error(request, "Aucune institution associée à votre profil.")
        return redirect('core:home')
    
    mon_institution = profil.institution
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            designation = request.POST.get('designation', '').strip()
            ordre_priorite = request.POST.get('ordre_priorite', '0')
            
            if not designation:
                messages.error(request, "La désignation de la fonction est requise.")
            else:
                try:
                    ordre_priorite = int(ordre_priorite)
                except ValueError:
                    ordre_priorite = 0
                
                # Vérifier si la fonction existe déjà
                if Fonction.objects.filter(designation__iexact=designation).exists():
                    messages.error(request, f"La fonction '{designation}' existe déjà.")
                else:
                    Fonction.objects.create(
                        designation=designation,
                        ordre_priorite=ordre_priorite
                    )
                    messages.success(request, f"Fonction '{designation}' ajoutée avec succès.")
                    return redirect('core:parametres_fonctions')
        
        elif action == 'delete':
            fonction_id = request.POST.get('fonction_id')
            try:
                fonction = Fonction.objects.get(uid=fonction_id)
                # Vérifier si la fonction est utilisée
                if fonction.membres.exists():
                    messages.error(request, f"Impossible de supprimer '{fonction.designation}' - elle est utilisée par des membres.")
                else:
                    designation = fonction.designation
                    fonction.delete()
                    messages.success(request, f"Fonction '{designation}' supprimée avec succès.")
                    return redirect('core:parametres_fonctions')
            except Fonction.DoesNotExist:
                messages.error(request, "Fonction non trouvée.")
        
        elif action == 'update':
            fonction_id = request.POST.get('fonction_id')
            designation = request.POST.get('designation', '').strip()
            ordre_priorite = request.POST.get('ordre_priorite', '0')
            
            if not designation:
                messages.error(request, "La désignation de la fonction est requise.")
            else:
                try:
                    ordre_priorite = int(ordre_priorite)
                except ValueError:
                    ordre_priorite = 0
                
                try:
                    fonction = Fonction.objects.get(uid=fonction_id)
                    fonction.designation = designation
                    fonction.ordre_priorite = ordre_priorite
                    fonction.save()
                    messages.success(request, f"Fonction '{designation}' mise à jour avec succès.")
                    return redirect('core:parametres_fonctions')
                except Fonction.DoesNotExist:
                    messages.error(request, "Fonction non trouvée.")
    
    # Récupérer toutes les fonctions
    fonctions = Fonction.objects.all().order_by('ordre_priorite', 'designation')
    
    return render(request, 'core/parametres_fonctions.html', {
        'mon_institution': mon_institution,
        'fonctions': fonctions,
        'user_role': 'sg',
    })


# FONCTION DÉSACTIVÉE - La création de comptes se fait uniquement lors de l'initialisation du ministère
# @login_required(login_url='/login/')
# @_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
# def creer_compte_entite(request):
#     """
#     DÉSACTIVÉ - Cette fonction permettait au SG de créer des comptes.
#     Maintenant, seule l'initialisation du ministère (setup_sisep) crée des comptes.
#     """
#     pass






@login_required(login_url='/login/')
def creer_compte_agent(request):
    """
    Crée un compte utilisateur lié à un agent existant.
    Accessible depuis la page de gestion des comptes.
    Le SG peut créer un compte et le lier à un agent qui existe déjà.
    
    Paramètres GET optionnels:
    - agent: UID de l'agent à présélectionner
    - chef_division: UID du Chef de Division (pour les divisions)
    - division: UID de la division (pour validation)
    """
    from gouvernance.models import Agent, Membre, Fonction, DivisionProvinciale
    
    try:
        profil = request.user.profil_sisep
    except ProfilUtilisateur.DoesNotExist:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    if not profil.institution:
        messages.error(request, "Aucune institution associée à votre profil.")
        return redirect('core:home')
    
    mon_institution = profil.institution
    
    # Vider les messages de la session si on vient d'une autre page
    # (pour éviter d'afficher les messages de divisions_provinciales)
    division_id = request.GET.get('division')
    if division_id:
        # Vider les messages existants
        storage = messages.get_messages(request)
        storage.used = True
    
    # Récupérer l'agent_id depuis les paramètres GET (optionnel)
    agent_id = request.GET.get('agent')
    chef_division_id = request.GET.get('chef_division')
    
    agent_preselectionne = None
    agent_email = None
    agent_fonction = None
    division_info = None
    role_force = None  # Rôle forcé pour les Chefs de Division
    
    # Vérifier que la division est active et a un chef assigné
    if division_id:
        try:
            division = DivisionProvinciale.objects.get(uid=division_id)
            if division.statut != 'ACTIVE':
                messages.error(request, "Cette division n'est pas active. Vous ne pouvez pas créer un compte pour une division inactive.")
                return redirect('core:home')
            if not division.chef:
                messages.error(request, "Cette division n'a pas de Chef assigné. Veuillez d'abord assigner un Chef de Division.")
                return redirect('gouvernance:divisions_provinciales')
            division_info = division
            role_force = 'DIRECTEUR_PROVINCIAL'  # Forcer le rôle pour les Chefs de Division
        except DivisionProvinciale.DoesNotExist:
            messages.error(request, "Division non trouvée.")
            return redirect('core:home')
    
    # Si chef_division_id est fourni, l'utiliser comme agent_id
    if chef_division_id and not agent_id:
        agent_id = chef_division_id
    
    if agent_id:
        agent_preselectionne = get_object_or_404(Agent, uid=agent_id, institution=mon_institution)
        agent_email = agent_preselectionne.personne.email
        
        # Récupérer la fonction de l'agent
        try:
            membre = Membre.objects.filter(
                personne=agent_preselectionne.personne,
                institution=mon_institution
            ).first()
            if membre:
                agent_fonction = membre.fonction.designation
        except:
            pass
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        agent_id = request.POST.get('agent_id', '').strip()
        role = request.POST.get('role', 'INSTITUTION_AGENT').strip()
        
        # Validations
        if not email:
            messages.error(request, "L'email est requis.")
            fonctions_agents = Fonction.objects.filter(
                membres__institution=mon_institution
            ).distinct().order_by('designation')
            return render(request, 'core/creer_compte_agent.html', {
                'mon_institution': mon_institution,
                'agents_disponibles': Agent.objects.filter(institution=mon_institution).exclude(
                    uid__in=ProfilUtilisateur.objects.filter(institution=mon_institution).values_list('personne_id', flat=True)
                ).select_related('personne').order_by('personne__nom', 'personne__prenom'),
                'agent_preselectionne': agent_preselectionne,
                'agent_email': agent_email,
                'agent_fonction': agent_fonction,
                'fonctions_agents': fonctions_agents,
                'role_force': role_force,
            })
        
        if not agent_id:
            messages.error(request, "Veuillez sélectionner un agent.")
            fonctions_agents = Fonction.objects.filter(
                membres__institution=mon_institution
            ).distinct().order_by('designation')
            return render(request, 'core/creer_compte_agent.html', {
                'mon_institution': mon_institution,
                'agents_disponibles': Agent.objects.filter(institution=mon_institution).exclude(
                    uid__in=ProfilUtilisateur.objects.filter(institution=mon_institution).values_list('personne_id', flat=True)
                ).select_related('personne').order_by('personne__nom', 'personne__prenom'),
                'agent_preselectionne': agent_preselectionne,
                'agent_email': agent_email,
                'agent_fonction': agent_fonction,
                'fonctions_agents': fonctions_agents,
                'role_force': role_force,
            })
        
        # Vérifier que l'agent existe et appartient à mon institution
        try:
            agent = Agent.objects.get(uid=agent_id, institution=mon_institution)
        except Agent.DoesNotExist:
            messages.error(request, "Agent non trouvé ou n'appartient pas à votre institution.")
            fonctions_agents = Fonction.objects.filter(
                membres__institution=mon_institution
            ).distinct().order_by('designation')
            return render(request, 'core/creer_compte_agent.html', {
                'mon_institution': mon_institution,
                'agents_disponibles': Agent.objects.filter(institution=mon_institution).exclude(
                    uid__in=ProfilUtilisateur.objects.filter(institution=mon_institution).values_list('personne_id', flat=True)
                ).select_related('personne').order_by('personne__nom', 'personne__prenom'),
                'agent_preselectionne': agent_preselectionne,
                'agent_email': agent_email,
                'agent_fonction': agent_fonction,
                'fonctions_agents': fonctions_agents,
                'role_force': role_force,
            })
        
        # Vérifier que l'email n'existe pas déjà
        if User.objects.filter(email=email).exists():
            messages.error(request, "Cet email est déjà utilisé.")
            fonctions_agents = Fonction.objects.filter(
                membres__institution=mon_institution
            ).distinct().order_by('designation')
            return render(request, 'core/creer_compte_agent.html', {
                'mon_institution': mon_institution,
                'agents_disponibles': Agent.objects.filter(institution=mon_institution).exclude(
                    uid__in=ProfilUtilisateur.objects.filter(institution=mon_institution).values_list('personne_id', flat=True)
                ).select_related('personne').order_by('personne__nom', 'personne__prenom'),
                'agent_preselectionne': agent_preselectionne,
                'agent_email': agent_email,
                'agent_fonction': agent_fonction,
                'fonctions_agents': fonctions_agents,
                'role_force': role_force,
            })
        
        # Vérifier les rôles uniques (Ministre, Secrétaire Général)
        unique_roles = ['MINISTRE', 'SECRETAIRE_GENERAL']
        if role in unique_roles:
            existing_count = ProfilUtilisateur.objects.filter(
                institution=mon_institution,
                role=role
            ).count()
            if existing_count > 0:
                role_label = 'Ministre' if role == 'MINISTRE' else 'Secrétaire Général'
                messages.error(request, f"Un compte {role_label} existe déjà dans cette institution.")
                fonctions_agents = Fonction.objects.filter(
                    membres__institution=mon_institution
                ).distinct().order_by('designation')
                return render(request, 'core/creer_compte_agent.html', {
                    'mon_institution': mon_institution,
                    'agents_disponibles': Agent.objects.filter(institution=mon_institution).exclude(
                        uid__in=ProfilUtilisateur.objects.filter(institution=mon_institution).values_list('personne_id', flat=True)
                    ).select_related('personne').order_by('personne__nom', 'personne__prenom'),
                    'agent_preselectionne': agent_preselectionne,
                    'agent_email': agent_email,
                    'agent_fonction': agent_fonction,
                    'fonctions_agents': fonctions_agents,
                    'role_force': role_force,
                })
        
        # Créer le compte utilisateur
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Creating account for agent: {agent.personne.nom} {agent.personne.prenom}")
            
            with transaction.atomic():
                username = email
                if User.objects.filter(username=username).exists():
                    username = f"{email.split('@')[0]}_{secrets.token_hex(4)}"
                
                logger.debug(f"Creating user with username: {username}, email: {email}")
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=agent.personne.prenom or agent.personne.nom,
                    last_name=agent.personne.nom,
                    password=secrets.token_urlsafe(32),
                    is_active=False,
                    is_staff=False,
                    is_superuser=False,
                )
                
                logger.debug(f"User created: {user.id}")
                
                # Créer le profil utilisateur
                profil_data = {
                    'user': user,
                    'personne': agent.personne,
                    'institution': mon_institution,
                    'role': role,
                    'actif': True,
                }
                
                # Si c'est un Directeur Provincial, lier à l'agent et à la province
                if role == 'DIRECTEUR_PROVINCIAL' and division_info:
                    profil_data['agent'] = agent
                    profil_data['province_admin'] = division_info.province
                    logger.debug(f"Linking Directeur Provincial to agent {agent.uid} and province {division_info.province.uid}")
                
                ProfilUtilisateur.objects.create(**profil_data)
                logger.debug(f"Profile created for user {user.id}")
                
                # Envoyer l'email de vérification
                try:
                    logger.info(f"Attempting to send verification email to {user.email}")
                    _envoyer_email_verification(user, request, f"Agent - {agent.personne.nom} {agent.personne.prenom}")
                    email_sent = True
                    logger.info(f"Verification email sent successfully to {user.email}")
                except Exception as email_error:
                    # Log l'erreur mais ne bloque pas la création du compte
                    logger.error(f"Erreur lors de l'envoi de l'email: {email_error}", exc_info=True)
                    email_sent = False
                
                if email_sent:
                    messages.success(request, f"Compte créé pour {agent.personne.nom} {agent.personne.prenom}. Un email de vérification a été envoyé.")
                else:
                    messages.warning(request, f"Compte créé pour {agent.personne.nom} {agent.personne.prenom}. Attention: L'email de vérification n'a pas pu être envoyé.")
                
                return redirect('core:gerer_comptes')
        except Exception as e:
            messages.error(request, f"Erreur lors de la création du compte : {e}")
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur création compte: {e}", exc_info=True)
    
    # Récupérer les agents disponibles (sans compte utilisateur)
    agents_disponibles = Agent.objects.filter(
        institution=mon_institution
    ).exclude(
        uid__in=ProfilUtilisateur.objects.filter(
            institution=mon_institution
        ).values_list('personne_id', flat=True)
    ).select_related('personne').order_by('personne__nom', 'personne__prenom')
    
    # Récupérer les fonctions disponibles pour les agents
    fonctions_agents = Fonction.objects.filter(
        membres__institution=mon_institution
    ).distinct().order_by('designation')
    
    return render(request, 'core/creer_compte_agent.html', {
        'mon_institution': mon_institution,
        'agents_disponibles': agents_disponibles,
        'agent_preselectionne': agent_preselectionne,
        'agent_email': agent_email,
        'agent_fonction': agent_fonction,
        'fonctions_agents': fonctions_agents,
        'role_force': role_force,
    })


@login_required(login_url='/login/')
@require_http_methods(['POST'])
def api_toggle_compte(request, user_id):
    """
    API endpoint pour activer/désactiver un compte.
    """
    try:
        profil = request.user.profil_sisep
    except ProfilUtilisateur.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil non trouvé'}, status=403)
    
    if not profil.institution:
        return JsonResponse({'success': False, 'error': 'Institution non trouvée'}, status=403)
    
    # Vérifier que l'utilisateur à modifier appartient à la même institution
    try:
        user_to_toggle = User.objects.get(id=user_id)
        profil_to_toggle = ProfilUtilisateur.objects.get(user=user_to_toggle)
        
        if profil_to_toggle.institution != profil.institution:
            return JsonResponse({'success': False, 'error': 'Accès refusé'}, status=403)
        
        # Basculer le statut
        user_to_toggle.is_active = not user_to_toggle.is_active
        user_to_toggle.save()
        
        return JsonResponse({
            'success': True,
            'is_active': user_to_toggle.is_active,
            'message': 'Compte activé' if user_to_toggle.is_active else 'Compte désactivé'
        })
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Utilisateur non trouvé'}, status=404)
    except ProfilUtilisateur.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required(login_url='/login/')
@require_http_methods(['POST'])
def api_delete_compte(request, user_id):
    """
    API endpoint pour supprimer un compte.
    """
    try:
        profil = request.user.profil_sisep
    except ProfilUtilisateur.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil non trouvé'}, status=403)
    
    if not profil.institution:
        return JsonResponse({'success': False, 'error': 'Institution non trouvée'}, status=403)
    
    # Vérifier que l'utilisateur à supprimer appartient à la même institution
    try:
        user_to_delete = User.objects.get(id=user_id)
        profil_to_delete = ProfilUtilisateur.objects.get(user=user_to_delete)
        
        if profil_to_delete.institution != profil.institution:
            return JsonResponse({'success': False, 'error': 'Accès refusé'}, status=403)
        
        # Supprimer le profil et l'utilisateur
        with transaction.atomic():
            profil_to_delete.delete()
            user_to_delete.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Compte supprimé avec succès'
        })
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Utilisateur non trouvé'}, status=404)
    except ProfilUtilisateur.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required(login_url='/login/')
@require_http_methods(['GET'])
def api_agents_disponibles(request):
    """
    API endpoint pour récupérer les agents disponibles d'une institution.
    Exclut les agents avec les rôles MINISTRE et SECRETAIRE_GENERAL.
    """
    from gouvernance.models import Agent
    from django.db.models import Q
    
    try:
        profil = request.user.profil_sisep
    except ProfilUtilisateur.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil non trouvé'}, status=403)
    
    if not profil.institution:
        return JsonResponse({'success': False, 'error': 'Institution non trouvée'}, status=403)
    
    # Récupérer les agents de l'institution
    agents = Agent.objects.filter(
        institution=profil.institution
    ).select_related('personne')
    
    # Exclure les agents avec les rôles MINISTRE ou SECRETAIRE_GENERAL
    restricted_roles = [RoleUtilisateur.MINISTRE, RoleUtilisateur.INSTITUTION_ADMIN]
    agents = agents.exclude(
        personne__profils_utilisateur__role__in=restricted_roles
    ).distinct().order_by('personne__nom', 'personne__prenom')
    
    agents_data = [
        {
            'uid': str(agent.uid),
            'nom_complet': agent.personne.nom_complet,
            'matricule': agent.matricule or 'N/A',
            'email': agent.personne.email or ''
        }
        for agent in agents
    ]
    
    return JsonResponse({
        'success': True,
        'agents': agents_data
    })


@login_required(login_url='/login/')
def profil_compte(request, user_id):
    """
    Affiche le profil d'un compte avec les informations de l'agent lié.
    """
    try:
        profil = request.user.profil_sisep
    except ProfilUtilisateur.DoesNotExist:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    if not profil.institution:
        messages.error(request, "Aucune institution associée à votre profil.")
        return redirect('core:home')
    
    try:
        user_compte = User.objects.get(id=user_id)
        profil_compte = ProfilUtilisateur.objects.get(user=user_compte)
        
        # Vérifier que le compte appartient à la même institution
        if profil_compte.institution != profil.institution:
            messages.error(request, "Accès refusé.")
            return redirect('core:gerer_comptes')
        
        # Récupérer les informations de l'agent lié
        agent_lie = profil_compte.agent
        
        return render(request, 'core/profil_compte.html', {
            'mon_institution': profil.institution,
            'profil_compte': profil_compte,
            'agent_lie': agent_lie,
            'user_role': profil.get_role_display().lower().replace(' ', '_') if profil.role else None,
        })
    
    except User.DoesNotExist:
        messages.error(request, "Compte non trouvé.")
        return redirect('core:gerer_comptes')
    except ProfilUtilisateur.DoesNotExist:
        messages.error(request, "Profil non trouvé.")
        return redirect('core:gerer_comptes')


@login_required(login_url='/login/')
@require_http_methods(['POST'])
def api_lier_agent(request, user_id):
    """
    API endpoint pour lier/délier un compte à un agent.
    """
    from gouvernance.models import Agent
    
    try:
        profil = request.user.profil_sisep
    except ProfilUtilisateur.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil non trouvé'}, status=403)
    
    if not profil.institution:
        return JsonResponse({'success': False, 'error': 'Institution non trouvée'}, status=403)
    
    try:
        user_to_link = User.objects.get(id=user_id)
        profil_to_link = ProfilUtilisateur.objects.get(user=user_to_link)
        
        if profil_to_link.institution != profil.institution:
            return JsonResponse({'success': False, 'error': 'Accès refusé'}, status=403)
        
        agent_id = request.POST.get('agent_id', '').strip()
        
        if not agent_id:
            # Délier l'agent
            profil_to_link.agent = None
            profil_to_link.save()
            return JsonResponse({
                'success': True,
                'message': 'Agent délié avec succès'
            })
        else:
            # Lier l'agent
            try:
                agent = Agent.objects.get(uid=agent_id, institution=profil.institution)
                profil_to_link.agent = agent
                profil_to_link.save()
                return JsonResponse({
                    'success': True,
                    'message': f'Compte lié à {agent.personne.nom_complet}'
                })
            except Agent.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Agent non trouvé'}, status=404)
    
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Utilisateur non trouvé'}, status=404)
    except ProfilUtilisateur.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
