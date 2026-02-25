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
)
from .models import ProfilUtilisateur, RoleUtilisateur, EmailVerificationToken
from .permissions import peut_acceder_setup_sisep, est_secretaire_general_ministere, est_ministre
from .forms import SetupInitialForm, SetPasswordVerificationForm, FederationRegistrationForm, CreerCompteEntiteForm

User = get_user_model()

CODE_MINISTERE = 'MIN-SPORTS'


def _envoyer_email_verification(user, request, role_label):
    """Crée un token de vérification, envoie l'e-mail avec le lien d'activation."""
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
    email = EmailMultiAlternatives(
        subject,
        text_body,
        getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@sisep-sport.gouv.cd'),
        [user.email],
    )
    email.attach_alternative(html_body, 'text/html')
    email.send(fail_silently=False)


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
    redirect_authenticated_user = True

    def get_success_url(self):
        next_url = self.get_redirect_url()
        if next_url:
            return next_url
        try:
            profil = self.request.user.profil_sisep
            if profil.actif and profil.role == RoleUtilisateur.SYSTEM_SUPER_ADMIN:
                return reverse('core:setup_sisep')
            if profil.actif and profil.role == RoleUtilisateur.INSTITUTION_ADMIN and profil.institution_id and getattr(profil.institution, 'institution_tutelle_id', None) is None:
                return reverse('core:sg_dashboard')
            if profil.actif and profil.role == RoleUtilisateur.MINISTRE:
                return reverse('core:minister_dashboard')
        except ProfilUtilisateur.DoesNotExist:
            pass
        return reverse('core:home')


def home(request):
    if not request.user.is_authenticated:
        return redirect('core:login')
    try:
        profil = request.user.profil_sisep
        if profil.actif and profil.role == RoleUtilisateur.SYSTEM_SUPER_ADMIN:
            return redirect('core:setup_sisep')
        if profil.actif and profil.role == RoleUtilisateur.INSTITUTION_ADMIN and profil.institution_id and getattr(profil.institution, 'institution_tutelle_id', None) is None:
            return redirect('core:sg_dashboard')
        if profil.actif and profil.role == RoleUtilisateur.MINISTRE:
            return redirect('core:minister_dashboard')
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
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
def creer_compte_entite(request):
    """
    Le Secrétaire Général crée un compte pour : Directeur de Cabinet,
    Direction provinciale (avec choix de province), ou Inspection générale.
    Validation par e-mail : l'utilisateur reçoit un lien pour activer et définir son mot de passe.
    """
    ministere = _get_ministere_racine()
    if not ministere:
        messages.error(request, "Aucun ministère trouvé. Effectuez d'abord l'initialisation du système.")
        return redirect('core:home')

    if request.method == 'POST' and request.POST.get('form_type') == 'creer_compte':
        form = CreerCompteEntiteForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            type_entite = cd['type_entite']
            nom_complet = cd['nom'].strip()
            email = cd['email'].strip().lower()
            province = cd.get('province')

            labels = {
                RoleUtilisateur.DIRECTEUR_CABINET: 'Directeur de Cabinet',
                RoleUtilisateur.DIRECTEUR_PROVINCIAL: 'Direction provinciale',
                RoleUtilisateur.INSPECTEUR_GENERAL: 'Inspection générale',
            }
            role_sisep = type_entite
            role_label = labels.get(role_sisep, type_entite)

            if User.objects.filter(email=email).exists():
                messages.error(request, f"Un compte avec l'e-mail « {email} » existe déjà.")
                return render(request, 'core/creer_compte_entite.html', {
                    'ministere': ministere,
                    'form': form,
                    'user_role': 'sg',
                })

            parts = nom_complet.split(None, 1)
            prenom = parts[1] if len(parts) > 1 else ''
            nom = parts[0] if parts else email.split('@')[0]

            try:
                with transaction.atomic():
                    personne = Personne.objects.create(
                        nom=nom, postnom='', prenom=prenom, email=email,
                    )
                    fct, _ = Fonction.objects.get_or_create(
                        designation=role_label,
                        defaults={'ordre_priorite': 0},
                    )
                    membre = Membre.objects.create(
                        personne=personne,
                        institution=ministere,
                        fonction=fct,
                    )
                    Mandat.objects.create(
                        membre=membre,
                        date_debut=date.today(),
                        statut_mandat='En cours',
                    )
                    username = email
                    if User.objects.filter(username=username).exists():
                        username = f"{email.split('@')[0]}_{type_entite[:3].upper()}"
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        first_name=prenom or nom,
                        last_name=nom,
                        password=secrets.token_urlsafe(32),
                        is_staff=False,
                        is_active=False,
                        is_superuser=False,
                    )
                    profil_kw = {
                        'user': user,
                        'personne': personne,
                        'institution': ministere,
                        'role': role_sisep,
                        'actif': True,
                    }
                    if role_sisep == RoleUtilisateur.DIRECTEUR_PROVINCIAL and province:
                        profil_kw['province_admin'] = province
                    ProfilUtilisateur.objects.create(**profil_kw)
                    _envoyer_email_verification(user, request, role_label)
                messages.success(
                    request,
                    f"Compte « {role_label} » créé pour {email}. Un e-mail d'activation a été envoyé.",
                )
                return redirect('core:creer_compte_entite')
            except Exception as e:
                messages.error(request, f"Erreur lors de la création du compte : {e}")
    else:
        form = CreerCompteEntiteForm()

    return render(request, 'core/creer_compte_entite.html', {
        'ministere': ministere,
        'form': form,
        'user_role': 'sg',
    })


@login_required(login_url='/login/')
@_user_passes_test(est_ministre, login_url='/login/')
def minister_dashboard(request):
    """
    Tableau de bord Ministre : institutions (fédérations) en attente de signature.
    Boutons de validation en Jaune #FDE015 (action importante).
    """
    en_attente = Institution.objects.filter(
        statut_signature='ATTENTE_SIGNATURE',
    ).select_related('type_institution', 'institution_tutelle').order_by('nom_officiel')

    return render(request, 'core/minister_dashboard.html', {
        'en_attente': en_attente,
        'user_role': 'ministre',
    })


@login_required(login_url='/login/')
@_user_passes_test(est_ministre, login_url='/login/')
@require_http_methods(['POST'])
def minister_sign_action(request, uid):
    """Action Ministre : signer (SIGNE) ou refuser (REFUSE) une institution en attente."""
    institution = get_object_or_404(Institution, uid=uid)
    if institution.statut_signature != 'ATTENTE_SIGNATURE':
        messages.warning(request, "Cette institution n'est plus en attente de signature.")
        return redirect('core:minister_dashboard')
    action = request.POST.get('action')
    if action == 'signer':
        institution.statut_signature = 'SIGNE'
        institution.statut_validee = True
        institution.statut_activation = 'ACTIVE'
        institution.save()
        messages.success(request, f"« {institution.nom_officiel} » a été signée et activée.")
    elif action == 'refuser':
        institution.statut_signature = 'REFUSE'
        institution.save()
        messages.info(request, f"« {institution.nom_officiel} » a été refusée.")
    else:
        messages.error(request, "Action invalide.")
    return redirect('core:minister_dashboard')


def _institutions_for_province(province_id):
    """Retourne les IDs d'institutions ayant au moins une adresse dans la province donnée."""
    if not province_id:
        return None
    return list(
        Institution.objects.filter(
            adresses_contact__quartier_village__groupement__secteur__territoire__province_admin_id=province_id
        ).values_list('uid', flat=True).distinct()
    )


@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
def sg_dashboard(request):
    """
    Dashboard du Secrétaire Général : widgets de performance, parapheur technique,
    filtre territorial (Province), quick-action par code d'homologation.
    """
    ministere = _get_ministere_racine()
    if not ministere:
        messages.error(request, "Aucun ministère trouvé. Effectuez d'abord l'initialisation du système.")
        return redirect('core:home')

    province_id = request.GET.get('province', '').strip() or None
    quick_q = request.GET.get('q', '').strip()

    # Filtre territorial : IDs d'institutions de la province (ou None = toutes)
    inst_ids_province = _institutions_for_province(province_id) if province_id else None

    base_fed = Institution.objects.filter(
        institution_tutelle=ministere,
        type_institution__code='FEDERATION',
    )
    if inst_ids_province is not None:
        base_fed = base_fed.filter(uid__in=inst_ids_province)

    # Card 1 : Fédérations actives (type FEDE, statut validé / actif)
    fed_actives = base_fed.filter(statut_validee=True, statut_activation='ACTIVE').count()

    # Card 2 : Dossiers en attente (demandes d'agrément avec statut EN_INSTRUCTION)
    base_inst = Institution.objects.all()
    if inst_ids_province is not None:
        base_inst = base_inst.filter(uid__in=inst_ids_province)
    dossiers_attente = base_inst.filter(
        etat_administrative__etat_agrement__code='EN_INSTRUCTION'
    ).count()

    # Card 3 : Alertes de conformité (mandats qui expirent dans < 3 mois)
    in_3_months = date.today() + timedelta(days=90)
    alertes_mandats = Mandat.objects.filter(
        date_fin__isnull=False,
        date_fin__gte=date.today(),
        date_fin__lte=in_3_months,
        statut_mandat__icontains='cours',
    ).count()

    # Card 4 : Utilisateurs connectés (personnels administratifs actifs)
    users_actifs = User.objects.filter(is_active=True).count()

    # Parapheur : 10 dernières "demandes" (institutions avec agrément, ordre par date)
    parapheur_qs = Institution.objects.filter(
        etat_administrative__isnull=False
    ).select_related(
        'type_institution',
        'etat_administrative',
        'etat_administrative__etat_agrement',
    ).order_by('-etat_administrative__date_delivrance', '-etat_administrative__uid')[:10]
    if inst_ids_province is not None:
        parapheur_qs = parapheur_qs.filter(uid__in=inst_ids_province)
    parapheur = list(parapheur_qs)

    # Quick-action : recherche par code d'homologation (ex: RDC-FED-001)
    if quick_q:
        match = Institution.objects.filter(code__icontains=quick_q).first()
        if match:
            messages.info(request, f"Fédération trouvée : {match.nom_officiel} ({match.code}).")
        else:
            messages.warning(request, f"Aucune institution avec le code « {quick_q} ».")

    provinces = ProvAdmin.objects.all().order_by('designation')

    return render(request, 'core/sg_dashboard.html', {
        'ministere': ministere,
        'fed_actives': fed_actives,
        'dossiers_attente': dossiers_attente,
        'alertes_mandats': alertes_mandats,
        'users_actifs': users_actifs,
        'parapheur': parapheur,
        'provinces': provinces,
        'province_id': province_id or '',
        'quick_q': quick_q,
    })
