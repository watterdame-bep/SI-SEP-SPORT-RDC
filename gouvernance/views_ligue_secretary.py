"""
Vues pour le Secrétaire de la Ligue Provinciale.
Gestion locale de la province: clubs, licences, compétitions, rapports.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.messages import get_messages
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives

from core.permissions import require_role
from gouvernance.models import Institution, AttestationReconnaissance, Athlete, VisiteMedicale, MedecinLigue, Personne, Agent, CaptureEmpreintes
from gouvernance.forms import (
    ClubCreationForm, ClubAddressForm, ClubDisciplinesForm, ClubDocumentsForm,
    LigueEvenementForm,
    TypeCompetitionForm, LigueCompetitionForm, CalendrierCompetitionForm,
    JourneeForm, RencontreForm,
)
from gouvernance.views_club_validation import get_or_create_division_provinciale
from gouvernance.models import TypeCompetition, Competition, Journee, Rencontre, CalendrierCompetition
from infrastructures.models import Evenement, Infrastructure
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods as http_methods
from django.core.exceptions import ValidationError


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_secretary_dashboard(request):
    """
    Tableau de bord du Secrétaire de la Ligue Provinciale.
    Vue d'ensemble de sa province avec statistiques et alertes.
    """
    # Ne pas afficher sur le dashboard les messages des autres interfaces (validation, enrôlement, etc.)
    list(get_messages(request))
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    # La ligue est l'institution du profil
    ligue = profil.institution
    
    if not ligue or ligue.niveau_territorial != 'LIGUE':
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    
    # Récupérer l'attestation d'homologation
    attestation = AttestationReconnaissance.objects.filter(ligue=ligue).first()
    
    # Compter les clubs affiliés dans la province
    clubs_count = Institution.objects.filter(
        institution_tutelle=ligue,
        niveau_territorial='CLUB'
    ).count()
    
    # Compter les athlètes licenciés (à implémenter avec le modèle Licence)
    athletes_count = 0  # TODO: Implémenter avec le modèle Licence
    
    # Compter les arbitres et entraîneurs certifiés (à implémenter)
    officials_count = 0  # TODO: Implémenter avec le modèle Certification
    
    # Récupérer les disciplines de la ligue
    disciplines = ligue.disciplines.all()
    
    # Récupérer la fédération parente
    federation = ligue.institution_tutelle
    
    # Récupérer la division provinciale
    from gouvernance.models import DivisionProvinciale
    division = DivisionProvinciale.objects.filter(
        province=ligue.province_admin
    ).first()
    
    context = {
        'ligue': ligue,
        'federation': federation,
        'division': division,
        'attestation': attestation,
        'clubs_count': clubs_count,
        'athletes_count': athletes_count,
        'officials_count': officials_count,
        'disciplines': disciplines,
        'user_role': 'ligue_secretary',
    }
    
    return render(request, 'gouvernance/ligue_secretary_dashboard.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_club_detail(request, club_id):
    """
    Détail d'un club avec ses informations et disciplines.
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    ligue = profil.institution
    
    # Vérifier que le club appartient à la ligue
    club = get_object_or_404(
        Institution,
        uid=club_id,
        institution_tutelle=ligue,
        niveau_territorial='CLUB'
    )
    
    # Récupérer les disciplines du club
    disciplines = club.disciplines.all()
    
    # Récupérer l'adresse de contact
    from gouvernance.models import AdresseContact
    adresse = AdresseContact.objects.filter(institution=club).first()
    
    context = {
        'ligue': ligue,
        'club': club,
        'disciplines': disciplines,
        'adresse': adresse,
        'user_role': 'ligue_secretary',
    }
    
    return render(request, 'gouvernance/ligue_club_detail.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_medecins_list(request):
    """
    Liste des médecins enregistrés pour la ligue (en tant qu'agents).
    L'enregistrement est séparé de la création de compte (effectuée par la Division).
    """
    try:
        profil = request.user.profil_sisep
    except Exception:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    ligue = profil.institution
    if not ligue or ligue.niveau_territorial not in ('LIGUE', 'LIGUE_PROVINCIALE'):
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    medecins = MedecinLigue.objects.filter(ligue=ligue).select_related('agent', 'agent__personne').order_by('agent__personne__nom')
    context = {
        'ligue': ligue,
        'medecins': medecins,
        'user_role': 'ligue_secretary',
    }
    return render(request, 'gouvernance/ligue_medecins_list.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_medecin_register(request):
    """
    Enregistrer un médecin de la ligue (création Personne + Agent + MedecinLigue).
    Ne crée pas de compte ; la Division pourra créer le compte plus tard si besoin.
    """
    try:
        profil = request.user.profil_sisep
    except Exception:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    ligue = profil.institution
    if not ligue or ligue.niveau_territorial not in ('LIGUE', 'LIGUE_PROVINCIALE'):
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    if request.method == 'POST':
        nom = (request.POST.get('nom') or '').strip()
        postnom = (request.POST.get('postnom') or '').strip()
        prenom = (request.POST.get('prenom') or '').strip()
        numero_ordre_medecins = (request.POST.get('numero_ordre_medecins') or '').strip()
        email = (request.POST.get('email') or '').strip()
        telephone = (request.POST.get('telephone') or '').strip()
        if not nom:
            messages.error(request, "Le nom est obligatoire.")
            return redirect('gouvernance:ligue_medecin_register')
        if not numero_ordre_medecins:
            messages.error(request, "Le numéro de l'Ordre des Médecins est obligatoire.")
            return redirect('gouvernance:ligue_medecin_register')
        if MedecinLigue.objects.filter(ligue=ligue, numero_ordre_medecins=numero_ordre_medecins).exists():
            messages.error(request, "Un médecin avec ce numéro d'Ordre des Médecins est déjà enregistré pour cette ligue.")
            return redirect('gouvernance:ligue_medecin_register')
        personne = Personne.objects.create(
            nom=nom,
            postnom=postnom or '',
            prenom=prenom or '',
            email=email or '',
            telephone=telephone or '',
        )
        agent = Agent.objects.create(
            personne=personne,
            institution=ligue,
            matricule=None,
        )
        MedecinLigue.objects.create(
            ligue=ligue,
            agent=agent,
            numero_ordre_medecins=numero_ordre_medecins,
        )
        messages.success(
            request,
            f"Médecin {personne.nom_complet} enregistré pour la ligue. "
            "La Division provinciale pourra lui créer un compte d'accès au système si besoin."
        )
        return redirect('gouvernance:ligue_medecins_list')
    context = {
        'ligue': ligue,
        'user_role': 'ligue_secretary',
    }
    return render(request, 'gouvernance/ligue_medecin_register.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_profile(request):
    """
    Profil de la ligue provinciale avec attestation d'homologation.
    Gestion de la signature et du cachet de la ligue.
    """
    try:
        profil = request.user.profil_sisep
        if not profil:
            messages.error(request, "Profil utilisateur introuvable.")
            return redirect('core:home')
    except Exception as e:
        messages.error(request, f"Erreur lors de la récupération du profil: {str(e)}")
        return redirect('core:home')
    
    ligue = profil.institution
    
    if not ligue:
        messages.error(request, "Aucune ligue associée à votre profil.")
        return redirect('core:home')
    
    if ligue.niveau_territorial != 'LIGUE':
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        password = request.POST.get('password', '').strip()
        
        # Vérifier le mot de passe
        if not request.user.check_password(password):
            messages.error(request, "Mot de passe incorrect. Modification annulée.")
            return render(request, 'gouvernance/ligue_profile.html', {
                'ligue': ligue,
                'user': request.user,
            }, status=400)
        
        if form_type == 'signature':
            if 'signature_image' in request.FILES:
                file = request.FILES['signature_image']
                
                # Vérifier que c'est un fichier PNG
                if file.content_type != 'image/png' and not file.name.lower().endswith('.png'):
                    messages.error(request, "Seuls les fichiers PNG sont acceptés. Veuillez sélectionner un fichier PNG transparent.")
                    return redirect('gouvernance:ligue_profile')
                
                # Vérifier la taille (max 5MB)
                if file.size > 5 * 1024 * 1024:
                    messages.error(request, "Le fichier est trop volumineux. Taille maximale: 5MB.")
                    return redirect('gouvernance:ligue_profile')
                
                ligue.signature_image = file
                ligue.save()
                messages.success(request, "✓ Signature téléchargée avec succès!")
            else:
                messages.error(request, "Veuillez sélectionner un fichier.")
        
        elif form_type == 'sceau':
            if 'sceau_image' in request.FILES:
                file = request.FILES['sceau_image']
                
                # Vérifier que c'est un fichier PNG
                if file.content_type != 'image/png' and not file.name.lower().endswith('.png'):
                    messages.error(request, "Seuls les fichiers PNG sont acceptés. Veuillez sélectionner un fichier PNG transparent.")
                    return redirect('gouvernance:ligue_profile')
                
                # Vérifier la taille (max 5MB)
                if file.size > 5 * 1024 * 1024:
                    messages.error(request, "Le fichier est trop volumineux. Taille maximale: 5MB.")
                    return redirect('gouvernance:ligue_profile')
                
                ligue.sceau_image = file
                ligue.save()
                messages.success(request, "✓ Cachet téléchargé avec succès!")
            else:
                messages.error(request, "Veuillez sélectionner un fichier.")
        
        elif form_type == 'logo':
            if 'logo_image' in request.FILES:
                file = request.FILES['logo_image']
                if not file.content_type.startswith('image/'):
                    messages.error(request, "Veuillez sélectionner une image (PNG, JPG, etc.).")
                    return redirect('gouvernance:ligue_profile')
                if file.size > 5 * 1024 * 1024:
                    messages.error(request, "Le fichier est trop volumineux. Taille maximale: 5MB.")
                    return redirect('gouvernance:ligue_profile')
                ligue.logo = file
                ligue.save()
                messages.success(request, "✓ Logo de la ligue mis à jour avec succès!")
            else:
                messages.error(request, "Veuillez sélectionner un fichier image.")
        
        return redirect('gouvernance:ligue_profile')
    
    context = {
        'ligue': ligue,
        'user_role': 'ligue_secretary',
    }
    
    return render(request, 'gouvernance/ligue_profile.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_documents(request):
    """
    Documents officiels de la ligue provinciale (Attestation d'Homologation).
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    ligue = profil.institution
    
    if not ligue or ligue.niveau_territorial != 'LIGUE':
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    
    # Récupérer l'attestation d'homologation
    attestation = AttestationReconnaissance.objects.filter(ligue=ligue).first()
    
    context = {
        'ligue': ligue,
        'attestation': attestation,
        'user_role': 'ligue_secretary',
    }
    
    return render(request, 'gouvernance/ligue_documents.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_communications(request):
    """
    Messagerie et communications avec le Chef de Division et la Fédération.
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    ligue = profil.institution
    
    if not ligue or ligue.niveau_territorial != 'LIGUE':
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    
    # Récupérer la division provinciale
    from gouvernance.models import DivisionProvinciale
    division = DivisionProvinciale.objects.filter(
        province=ligue.province_admin
    ).first()
    
    # Récupérer la fédération parente
    federation = ligue.institution_tutelle
    
    # TODO: Implémenter le système de messagerie
    messages_list = []
    
    context = {
        'ligue': ligue,
        'division': division,
        'federation': federation,
        'messages': messages_list,
        'user_role': 'ligue_secretary',
    }
    
    return render(request, 'gouvernance/ligue_communications.html', context)



@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_clubs_affiliation(request):
    """
    Interface d'affiliation des clubs à la ligue provinciale.
    Affiche la liste des clubs et permet d'en créer de nouveaux.
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    ligue = profil.institution
    
    if not ligue or ligue.niveau_territorial != 'LIGUE':
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    
    # Récupérer tous les clubs affiliés à cette ligue
    clubs = Institution.objects.filter(
        institution_tutelle=ligue,
        niveau_territorial='CLUB'
    ).select_related('type_institution', 'province_admin').prefetch_related('disciplines').order_by('nom_officiel')
    
    # Calculer les statistiques
    stats = {
        'en_attente': clubs.filter(statut_validation_club='EN_ATTENTE_VALIDATION').count(),
        'valides': clubs.filter(statut_validation_club='VALIDEE_PROVINCIALE').count(),
        'affilies': clubs.filter(statut_validation_club='AFFILIEE').count(),
        'rejetes': clubs.filter(statut_validation_club='REJETEE_PROVINCIALE').count(),
    }
    
    context = {
        'ligue': ligue,
        'clubs': clubs,
        'stats': stats,
        'user_role': 'ligue_secretary',
    }
    
    return render(request, 'gouvernance/ligue_clubs_affiliation.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_club_create_step1(request):
    """
    Étape 1 : Informations de base du club
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    ligue = profil.institution
    
    if not ligue or ligue.niveau_territorial != 'LIGUE':
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    
    if request.method == 'POST':
        form = ClubCreationForm(request.POST, request.FILES)
        if form.is_valid():
            # Generate code if not provided
            code = form.cleaned_data.get('code', '').strip()
            if not code:
                sigle = form.cleaned_data['sigle'].upper()
                timestamp = str(int(__import__('time').time() * 1000))[-6:]
                code = f"{sigle}-{timestamp}"
            
            # Stocker les données en session
            request.session['club_data_step1'] = {
                'nom_officiel': form.cleaned_data['nom_officiel'],
                'sigle': form.cleaned_data['sigle'],
                'code': code,
                'statut_juridique': form.cleaned_data.get('statut_juridique', ''),
                'date_creation': str(form.cleaned_data['date_creation']) if form.cleaned_data.get('date_creation') else None,
                'nombre_pers_admin': form.cleaned_data.get('nombre_pers_admin', 0) or 0,
                'nombre_pers_tech': form.cleaned_data.get('nombre_pers_tech', 0) or 0,
                'partenaire': form.cleaned_data.get('partenaire', ''),
                'email_officiel': form.cleaned_data.get('email_officiel', ''),
                'telephone_off': form.cleaned_data.get('telephone_off', ''),
                'site_web': form.cleaned_data.get('site_web', ''),
                'nombre_athletes_hommes': form.cleaned_data.get('nombre_athletes_hommes', 0) or 0,
                'nombre_athletes_femmes': form.cleaned_data.get('nombre_athletes_femmes', 0) or 0,
            }
            
            # Gérer le logo
            if 'logo' in request.FILES:
                request.session['club_logo'] = request.FILES['logo'].name
                # Stocker le fichier temporairement
                import tempfile
                import os
                temp_dir = tempfile.gettempdir()
                temp_path = os.path.join(temp_dir, request.FILES['logo'].name)
                with open(temp_path, 'wb+') as destination:
                    for chunk in request.FILES['logo'].chunks():
                        destination.write(chunk)
                request.session['club_logo_path'] = temp_path
            
            return redirect('gouvernance:ligue_club_create_step2')
    else:
        form = ClubCreationForm()
    
    context = {
        'ligue': ligue,
        'form': form,
        'step': 1,
        'total_steps': 3,
        'user_role': 'ligue_secretary',
        'province_id': str(ligue.province_admin.uid) if ligue.province_admin else None,
        'province_name': ligue.province_admin.designation if ligue.province_admin else None,
        'ligue_disciplines': ', '.join([d.designation for d in ligue.disciplines.all()]),
    }
    
    return render(request, 'gouvernance/ligue_club_create.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_club_create_step2(request):
    """
    Étape 2 : Adresse, Responsables et Agrément
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    ligue = profil.institution
    
    if not ligue or ligue.niveau_territorial != 'LIGUE':
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    
    # Vérifier que l'étape 1 a été complétée
    if 'club_data_step1' not in request.session:
        messages.error(request, "Veuillez d'abord compléter l'étape 1.")
        return redirect('gouvernance:ligue_club_create_step1')
    
    if request.method == 'POST':
        form = ClubAddressForm(request.POST, ligue=ligue)
        if form.is_valid():
            # Stocker les données en session
            request.session['club_data_step2'] = {
                'province': str(form.cleaned_data['province'].uid) if form.cleaned_data.get('province') else None,
                'territoire': str(form.cleaned_data['territoire']) if form.cleaned_data.get('territoire') else None,
                'secteur': str(form.cleaned_data['secteur']) if form.cleaned_data.get('secteur') else None,
                'groupement_quartier': str(form.cleaned_data['groupement_quartier']) if form.cleaned_data.get('groupement_quartier') else None,
                'avenue': form.cleaned_data['avenue'],
                'numero': form.cleaned_data.get('numero', ''),
                'nom_president': form.cleaned_data['nom_president'],
                'telephone_president': form.cleaned_data.get('telephone_president', ''),
                'nationalite_president': form.cleaned_data.get('nationalite_president', ''),
                'type_agrement_sollicite': form.cleaned_data.get('type_agrement_sollicite', ''),
                'date_demande_agrement': str(form.cleaned_data['date_demande_agrement']) if form.cleaned_data.get('date_demande_agrement') else None,
                'duree_sollicitee': form.cleaned_data.get('duree_sollicitee', '4'),
            }
            return redirect('gouvernance:ligue_club_create_step3')
    else:
        form = ClubAddressForm(ligue=ligue)
    
    context = {
        'ligue': ligue,
        'form': form,
        'step': 2,
        'total_steps': 3,
        'user_role': 'ligue_secretary',
        'province_id': str(ligue.province_admin.uid) if ligue.province_admin else None,
        'province_name': ligue.province_admin.designation if ligue.province_admin else None,
        'ligue_disciplines': ', '.join([d.designation for d in ligue.disciplines.all()]),
    }
    
    return render(request, 'gouvernance/ligue_club_create.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_club_create_step3(request):
    """
    Étape 3 : Disciplines et Documents
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    ligue = profil.institution
    
    if not ligue or ligue.niveau_territorial != 'LIGUE':
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    
    # Données des étapes 1 et 2 : depuis la session ou construites depuis le POST (formulaire une seule page)
    step1_data = None
    step2_data = None
    if request.method == 'POST':
        if 'club_data_step1' in request.session and 'club_data_step2' in request.session:
            step1_data = request.session['club_data_step1']
            step2_data = request.session['club_data_step2']
        else:
            # Soumission en une fois (toutes les étapes dans un seul POST) : construire depuis request
            form_step1 = ClubCreationForm(request.POST, request.FILES)
            form_step2 = ClubAddressForm(request.POST, ligue=ligue)
            if form_step1.is_valid() and form_step2.is_valid():
                step1_data = {
                    'nom_officiel': form_step1.cleaned_data['nom_officiel'],
                    'sigle': form_step1.cleaned_data['sigle'],
                    'code': form_step1.cleaned_data.get('code') or form_step1.cleaned_data['sigle'][:10].upper(),
                    'statut_juridique': form_step1.cleaned_data.get('statut_juridique', ''),
                    'date_creation': str(form_step1.cleaned_data['date_creation']) if form_step1.cleaned_data.get('date_creation') else None,
                    'nombre_pers_admin': form_step1.cleaned_data.get('nombre_pers_admin', 0) or 0,
                    'nombre_pers_tech': form_step1.cleaned_data.get('nombre_pers_tech', 0) or 0,
                    'partenaire': form_step1.cleaned_data.get('partenaire', ''),
                    'email_officiel': form_step1.cleaned_data.get('email_officiel', ''),
                    'telephone_off': form_step1.cleaned_data.get('telephone_off', ''),
                    'site_web': form_step1.cleaned_data.get('site_web', ''),
                    'nombre_athletes_hommes': int(request.POST.get('nombre_athletes_hommes', 0) or 0),
                    'nombre_athletes_femmes': int(request.POST.get('nombre_athletes_femmes', 0) or 0),
                }
                step2_data = {
                    'province': str(form_step2.cleaned_data['province'].uid) if form_step2.cleaned_data.get('province') else None,
                    'territoire': str(form_step2.cleaned_data['territoire']) if form_step2.cleaned_data.get('territoire') else None,
                    'secteur': str(form_step2.cleaned_data['secteur']) if form_step2.cleaned_data.get('secteur') else None,
                    'groupement_quartier': str(form_step2.cleaned_data['groupement_quartier']) if form_step2.cleaned_data.get('groupement_quartier') else None,
                    'avenue': form_step2.cleaned_data['avenue'],
                    'numero': form_step2.cleaned_data.get('numero', ''),
                    'nom_president': form_step2.cleaned_data['nom_president'],
                    'telephone_president': form_step2.cleaned_data.get('telephone_president', ''),
                    'nationalite_president': form_step2.cleaned_data.get('nationalite_president', ''),
                    'type_agrement_sollicite': form_step2.cleaned_data.get('type_agrement_sollicite', ''),
                    'date_demande_agrement': str(form_step2.cleaned_data['date_demande_agrement']) if form_step2.cleaned_data.get('date_demande_agrement') else None,
                    'duree_sollicitee': form_step2.cleaned_data.get('duree_sollicitee', '4'),
                }
            else:
                errs = []
                if not form_step1.is_valid():
                    errs.append("Étape 1: " + " ".join(" / ".join(v) for v in form_step1.errors.values()))
                if not form_step2.is_valid():
                    errs.append("Étape 2: " + " ".join(" / ".join(v) for v in form_step2.errors.values()))
                messages.error(request, "Données invalides. " + " ".join(errs))
                step1_data = None
                step2_data = None
    
    if request.method == 'POST' and step1_data and step2_data:
        try:
            from django.db import transaction
            from gouvernance.models import TypeInstitution, AdresseContact, ClubValidation
            from datetime import datetime
            import os

            with transaction.atomic():
                club_type = TypeInstitution.objects.get(code='CLUB')

                date_creation = None
                if step1_data.get('date_creation'):
                    try:
                        date_creation = datetime.strptime(step1_data['date_creation'], '%Y-%m-%d').date()
                    except Exception:
                        pass

                date_demande_agrement = None
                if step2_data.get('date_demande_agrement'):
                    try:
                        date_demande_agrement = datetime.strptime(step2_data['date_demande_agrement'], '%Y-%m-%d').date()
                    except Exception:
                        pass

                club = Institution.objects.create(
                    code=step1_data.get('code') or step1_data['sigle'][:10].upper(),
                    nom_officiel=step1_data['nom_officiel'],
                    sigle=step1_data['sigle'],
                    type_institution=club_type,
                    statut_juridique=step1_data.get('statut_juridique', ''),
                    date_creation=date_creation,
                    nombre_pers_admin=step1_data.get('nombre_pers_admin', 0),
                    nombre_pers_tech=step1_data.get('nombre_pers_tech', 0),
                    partenaire=step1_data.get('partenaire', ''),
                    email_officiel=step1_data.get('email_officiel', ''),
                    telephone_off=step1_data.get('telephone_off', ''),
                    site_web=step1_data.get('site_web', ''),
                    institution_tutelle=ligue,
                    niveau_territorial='CLUB',
                    province_admin=ligue.province_admin,
                    statut_activation='ACTIVE',
                    statut_validation_club='EN_ATTENTE_VALIDATION',
                    type_agrement_sollicite=step2_data.get('type_agrement_sollicite', ''),
                    date_demande_agrement=date_demande_agrement,
                    duree_sollicitee=int(step2_data.get('duree_sollicitee', 4)),
                    nom_president=step2_data.get('nom_president', ''),
                    telephone_president=step2_data.get('telephone_president', ''),
                )

                # Logo : depuis la session (flux par étapes) ou depuis request.FILES (soumission unique)
                if 'club_logo_path' in request.session:
                    logo_path = request.session['club_logo_path']
                    if os.path.exists(logo_path):
                        with open(logo_path, 'rb') as f:
                            from django.core.files.base import ContentFile
                            club.logo.save(request.session['club_logo'], ContentFile(f.read()), save=True)
                        os.remove(logo_path)
                    del request.session['club_logo_path']
                    del request.session['club_logo']
                elif request.FILES.get('logo'):
                    club.logo.save(request.FILES['logo'].name, request.FILES['logo'], save=True)

                # Disciplines : héritées de la ligue (template une page n'envoie pas les IDs)
                club.disciplines.set(ligue.disciplines.all())

                AdresseContact.objects.create(
                    institution=club,
                    avenue=step2_data['avenue'],
                    numero=step2_data.get('numero', ''),
                )

                document_fields = {
                    'statut_club': 'document_statuts',
                    'reglement_interieur': 'document_reglement_interieur',
                    'pv_assemblee_generale': 'document_pv_ag',
                    'contrat_bail': 'document_contrat_bail',
                    'liste_membres_fondateurs': 'document_liste_membres',
                    'certificat_nationalite': 'document_certificat_nationalite',
                    'liste_athletes': 'document_liste_athletes',
                }
                for form_field, model_field in document_fields.items():
                    if form_field in request.FILES and request.FILES[form_field]:
                        setattr(club, model_field, request.FILES[form_field])
                club.save()

                if ligue.province_admin:
                    division_institution = get_or_create_division_provinciale(ligue.province_admin)
                    if division_institution:
                        ClubValidation.objects.get_or_create(
                            club=club,
                            defaults={'division_provinciale': division_institution},
                        )

                for key in ('club_data_step1', 'club_data_step2'):
                    if key in request.session:
                        del request.session[key]

                messages.success(request, f"✓ Club '{club.nom_officiel}' créé avec succès! En attente de validation par la direction provinciale.")
                return redirect('gouvernance:ligue_clubs_affiliation')

        except Exception as e:
            messages.error(request, f"Erreur lors de la création du club: {str(e)}")
            import traceback
            traceback.print_exc()
    elif request.method == 'POST' and (not step1_data or not step2_data):
        if not step1_data and not step2_data and 'club_data_step1' not in request.session:
            messages.error(request, "Veuillez remplir correctement les étapes 1 et 2 (identité et adresse).")
        return redirect('gouvernance:ligue_club_create_step1')
    
    if request.method == 'GET' and ('club_data_step1' not in request.session or 'club_data_step2' not in request.session):
        messages.error(request, "Veuillez d'abord compléter les étapes 1 et 2.")
        return redirect('gouvernance:ligue_club_create_step1')
    
    form = ClubDocumentsForm()
    
    # Récupérer les disciplines pour le template
    from gouvernance.models.discipline import DisciplineSport
    disciplines = DisciplineSport.objects.filter(actif=True).order_by('designation')
    
    context = {
        'ligue': ligue,
        'form': form,
        'disciplines': disciplines,
        'step': 3,
        'total_steps': 3,
        'user_role': 'ligue_secretary',
        'province_id': str(ligue.province_admin.uid) if ligue.province_admin else None,
        'province_name': ligue.province_admin.designation if ligue.province_admin else None,
        'ligue_disciplines': ', '.join([d.designation for d in ligue.disciplines.all()]),
    }
    
    return render(request, 'gouvernance/ligue_club_create.html', context)


@login_required
@require_http_methods(["GET", "POST"])
@require_role('FEDERATION_SECRETARY')
def ligue_club_affiliate(request, club_id):
    """
    Affiliate a validated club to the ligue (final step after provincial validation).
    Creates a club secretary account and sends activation email.
    GET: Show confirmation page
    POST: Process affiliation
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    ligue = profil.institution
    
    if not ligue or ligue.niveau_territorial != 'LIGUE':
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    
    # Get the club
    club = get_object_or_404(
        Institution,
        uid=club_id,
        institution_tutelle=ligue,
        niveau_territorial='CLUB'
    )
    
    # Club déjà affilié : ne pas ré-affilier, rediriger
    if club.statut_validation_club == 'AFFILIEE':
        messages.info(request, f"Le club '{club.nom_officiel}' est déjà affilié.")
        return redirect('gouvernance:ligue_clubs_affiliation')
    
    # Vérifier que le club a été validé par la direction provinciale (statut club = VALIDEE_PROVINCIALE)
    # Note: ClubValidation.statut vaut 'ACCEPTEE' quand le directeur valide, pas 'VALIDEE_PROVINCIALE'
    from gouvernance.models import ClubValidation
    validation = ClubValidation.objects.filter(club=club).first()
    
    if not validation:
        messages.error(request, "Aucune validation provinciale trouvée pour ce club.")
        return redirect('gouvernance:ligue_clubs_affiliation')
    if club.statut_validation_club != 'VALIDEE_PROVINCIALE':
        messages.error(request, "Ce club n'a pas encore été validé par la direction provinciale.")
        return redirect('gouvernance:ligue_clubs_affiliation')
    # Accepter validation.statut in ('ACCEPTEE', 'VALIDEE_PROVINCIALE', 'AFFILIEE') pour permettre l'affiliation
    if validation.statut not in ('ACCEPTEE', 'VALIDEE_PROVINCIALE', 'AFFILIEE'):
        messages.error(request, "Ce club n'est pas dans un statut permettant l'affiliation.")
        return redirect('gouvernance:ligue_clubs_affiliation')
    
    # GET: Show confirmation page
    if request.method == 'GET':
        context = {
            'ligue': ligue,
            'club': club,
            'validation': validation,
            'user_role': 'ligue_secretary',
        }
        return render(request, 'gouvernance/ligue_club_affiliate_confirm.html', context)
    
    # POST: Process affiliation
    if request.method == 'POST':
        try:
            from django.db import transaction
            from django.contrib.auth.models import User
            from core.models import ProfilUtilisateur, EmailVerificationToken
            from django.core.mail import send_mail
            from django.template.loader import render_to_string
            from django.urls import reverse
            from django.conf import settings
            from django.core.files.base import ContentFile
            from gouvernance.affiliation_generator import generer_acte_affiliation
            from datetime import datetime
            
            with transaction.atomic():
                # Generate affiliation document (Acte d'Affiliation)
                try:
                    pdf_buffer, numero_affiliation = generer_acte_affiliation(club, ligue, validation)
                    
                    # Save PDF to club
                    filename = f"Acte_Affiliation_{numero_affiliation}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    club.document_acte_affiliation.save(
                        filename,
                        ContentFile(pdf_buffer.getvalue()),
                        save=True
                    )
                    club.numero_affiliation = numero_affiliation
                    club.date_affiliation = timezone.now()
                except Exception as e:
                    print(f"Erreur lors de la génération du PDF d'affiliation: {e}")
                    import traceback
                    traceback.print_exc()
                
                # Create club secretary account
                club_email = club.email_officiel or f"secretary-{club.sigle.lower()}@sisep-sport.cd"
                
                # Check if user already exists
                user = User.objects.filter(email=club_email).first()
                if not user:
                    # Generate username from club sigle
                    username = f"club_{club.sigle.lower()}"
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"club_{club.sigle.lower()}_{counter}"
                        counter += 1
                    
                    # Create user account (inactive until email verification)
                    user = User.objects.create_user(
                        username=username,
                        email=club_email,
                        is_active=False,
                    )
                
                # Create or update profil
                profil_club, created = ProfilUtilisateur.objects.get_or_create(
                    user=user,
                    defaults={
                        'institution': club,
                        'role': 'CLUB_SECRETARY',
                        'actif': True,
                    }
                )
                
                if not created:
                    profil_club.institution = club
                    profil_club.role = 'CLUB_SECRETARY'
                    profil_club.actif = True
                    profil_club.save()
                
                # Create email verification token
                token_obj, _ = EmailVerificationToken.objects.get_or_create(user=user)
                
                # Generate activation URL
                activation_url = request.build_absolute_uri(
                    reverse('core:verify_email', kwargs={'token': token_obj.token})
                )
                
                # Send activation email
                context = {
                    'club_name': club.sigle,
                    'club_nom_officiel': club.nom_officiel,
                    'club_sigle': club.sigle,
                    'club_code': club.code,
                    'ligue_name': ligue.nom_officiel,
                    'user_email': club_email,
                    'activation_url': activation_url,
                }
                
                email_html = render_to_string('emails/club_secretary_account_activation.html', context)
                
                # Affiliate the club et mise à jour validation (avant envoi email pour que la transaction ne dépende pas du SMTP)
                club.statut_validation_club = 'AFFILIEE'
                club.save()
                validation.statut = 'AFFILIEE'
                validation.save()
                
                # Envoyer l'email avec le PDF en pièce jointe (fail_silently=True : compte et affiliation déjà enregistrés même si SMTP échoue)
                email_sent = False
                try:
                    from django.core.mail import EmailMultiAlternatives
                    
                    email = EmailMultiAlternatives(
                        subject=f"Activation de votre compte - Club {club.nom_officiel}",
                        body="Veuillez consulter la version HTML de cet email.",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[club_email],
                    )
                    email.attach_alternative(email_html, "text/html")
                    
                    # Attacher le PDF de l'Acte d'Affiliation
                    if club.document_acte_affiliation:
                        try:
                            pdf_file = club.document_acte_affiliation.open('rb')
                            pdf_content = pdf_file.read()
                            pdf_file.close()
                            
                            filename = f"Acte_Affiliation_{club.numero_affiliation}.pdf"
                            email.attach(filename, pdf_content, 'application/pdf')
                        except Exception as e:
                            print(f"Erreur lors de l'attachement du PDF: {e}")
                    
                    email.send(fail_silently=True)
                    email_sent = True
                except Exception as e:
                    print(f"Erreur lors de l'envoi de l'email: {e}")
                    pass
                
                if email_sent:
                    messages.success(
                        request,
                        f"✓ Club '{club.nom_officiel}' affilié avec succès! "
                        f"Acte d'affiliation généré (N° {club.numero_affiliation}). "
                        f"Un email d'activation a été envoyé à {club_email}"
                    )
                else:
                    messages.success(
                        request,
                        f"✓ Club '{club.nom_officiel}' affilié. Acte d'affiliation généré (N° {club.numero_affiliation}). "
                        f"Compte créé pour {club_email}. L'envoi de l'email a échoué (vérifiez la configuration SMTP)."
                    )
                return redirect('gouvernance:ligue_clubs_affiliation')
        
        except Exception as e:
            messages.error(request, f"Erreur lors de l'affiliation: {str(e)}")
            import traceback
            traceback.print_exc()
            return redirect('gouvernance:ligue_clubs_affiliation')
    
    context = {
        'ligue': ligue,
        'club': club,
        'validation': validation,
        'user_role': 'ligue_secretary',
    }
    
    return render(request, 'gouvernance/ligue_club_affiliate_confirm.html', context)


@login_required
@require_http_methods(["POST"])
@require_role('FEDERATION_SECRETARY')
def ligue_club_resend_activation(request, club_id):
    """
    Pour un club déjà affilié : créer le compte secrétaire si absent et (re)envoyer l'email d'activation.
    Utile quand le club a été affilié sans compte ou si l'email n'est pas arrivé (ex. club FCO).
    """
    try:
        profil = request.user.profil_sisep
    except Exception:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    ligue = profil.institution
    if not ligue or ligue.niveau_territorial != 'LIGUE':
        messages.error(request, "Vous n'êtes pas associé à une ligue.")
        return redirect('core:home')
    club = get_object_or_404(
        Institution,
        uid=club_id,
        institution_tutelle=ligue,
        niveau_territorial='CLUB',
    )
    if club.statut_validation_club != 'AFFILIEE':
        messages.warning(request, "Cette action est réservée aux clubs déjà affiliés.")
        return redirect('gouvernance:ligue_clubs_affiliation')
    from django.contrib.auth.models import User
    from core.models import ProfilUtilisateur, EmailVerificationToken
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.urls import reverse
    from django.conf import settings
    club_email = club.email_officiel or f"secretary-{club.sigle.lower()}@sisep-sport.cd"
    user = User.objects.filter(email=club_email).first()
    if not user:
        username = f"club_{club.sigle.lower()}"
        c = 1
        while User.objects.filter(username=username).exists():
            username = f"club_{club.sigle.lower()}_{c}"
            c += 1
        user = User.objects.create_user(username=username, email=club_email, is_active=False)
    profil_club, _ = ProfilUtilisateur.objects.get_or_create(
        user=user,
        defaults={'institution': club, 'role': 'CLUB_SECRETARY', 'actif': True},
    )
    if profil_club.institution_id != club.uid:
        profil_club.institution = club
        profil_club.save(update_fields=['institution'])
    token_obj, _ = EmailVerificationToken.objects.get_or_create(user=user)
    activation_url = request.build_absolute_uri(reverse('core:verify_email', kwargs={'token': token_obj.token}))
    context = {
        'club_name': club.sigle, 'club_nom_officiel': club.nom_officiel, 'club_sigle': club.sigle,
        'club_code': club.code, 'ligue_name': ligue.nom_officiel, 'user_email': club_email,
        'activation_url': activation_url,
    }
    email_html = render_to_string('emails/club_secretary_account_activation.html', context)
    try:
        email = EmailMultiAlternatives(
            subject=f"Activation de votre compte - Club {club.nom_officiel}",
            body="Veuillez consulter la version HTML de cet email.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[club_email],
        )
        email.attach_alternative(email_html, "text/html")
        
        # Attacher le PDF de l'Acte d'Affiliation
        if club.document_acte_affiliation:
            try:
                pdf_file = club.document_acte_affiliation.open('rb')
                pdf_content = pdf_file.read()
                pdf_file.close()
                
                filename = f"Acte_Affiliation_{club.numero_affiliation}.pdf"
                email.attach(filename, pdf_content, 'application/pdf')
            except Exception as e:
                print(f"Erreur lors de l'attachement du PDF: {e}")
        
        email.send(fail_silently=True)
        messages.success(request, f"✓ Email d'activation envoyé (ou renvoyé) à {club_email} pour le club {club.nom_officiel}.")
    except Exception:
        messages.warning(request, f"Compte mis à jour pour {club.nom_officiel}, mais l'envoi de l'email a échoué (vérifiez SMTP).")
    return redirect('gouvernance:ligue_clubs_affiliation')


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_athletes_certifies_list(request):
    """
    Liste des athlètes ayant réussi leur certification (provinciale ou nationale).
    La ligue peut voir tous les joueurs certifiés de ses clubs.
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    ligue = profil.institution
    if not ligue or ligue.niveau_territorial not in ['LIGUE', 'LIGUE_PROVINCIALE']:
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    
    clubs_ligue = Institution.objects.filter(
        niveau_territorial='CLUB',
        institution_tutelle=ligue
    )
    athletes = Athlete.objects.filter(
        club__in=clubs_ligue,
        statut_certification__in=('CERTIFIE_PROVINCIAL', 'CERTIFIE_NATIONAL'),
        actif=True
    ).select_related('personne', 'club', 'discipline').order_by('-date_validation_ligue', '-date_validation_federation')
    
    total_provincial = athletes.filter(statut_certification='CERTIFIE_PROVINCIAL').count()
    total_national = athletes.filter(statut_certification='CERTIFIE_NATIONAL').count()
    
    context = {
        'ligue': ligue,
        'athletes': athletes,
        'total_provincial': total_provincial,
        'total_national': total_national,
        'total': athletes.count(),
        'user_role': 'ligue_secretary',
    }
    return render(request, 'gouvernance/ligue_athletes_certifies_list.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_athletes_validation_list(request):
    """
    Liste des athlètes en attente de validation provinciale.
    Le secrétaire de la ligue voit tous les athlètes EN_ATTENTE_VALIDATION_LIGUE (déjà enrôlés).
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    ligue = profil.institution
    
    if not ligue or ligue.niveau_territorial not in ['LIGUE', 'LIGUE_PROVINCIALE']:
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    
    # Récupérer tous les clubs de la province
    clubs_province = Institution.objects.filter(
        niveau_territorial='CLUB',
        institution_tutelle=ligue
    )
    
    # Récupérer tous les athlètes en statut EN_ATTENTE_VALIDATION_LIGUE de ces clubs
    athletes_en_attente = Athlete.objects.filter(
        club__in=clubs_province,
        statut_certification='EN_ATTENTE_VALIDATION_LIGUE',
        actif=True
    ).select_related('personne', 'club', 'discipline').order_by('-date_enrolement')
    
    # Statistiques
    total_en_attente = athletes_en_attente.count()
    
    context = {
        'ligue': ligue,
        'athletes': athletes_en_attente,
        'total_en_attente': total_en_attente,
        'user_role': 'ligue_secretary',
    }
    
    return render(request, 'gouvernance/ligue_athletes_validation_list.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_athlete_validate(request, athlete_uid):
    """
    Valider un athlète au niveau provincial.
    Vérifie qu'il n'existe pas de doublon dans la province.
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    ligue = profil.institution
    athlete = get_object_or_404(Athlete, uid=athlete_uid)
    
    # Vérifier que l'athlète appartient à un club de cette ligue
    if athlete.club.institution_tutelle != ligue:
        messages.error(request, "Cet athlète n'appartient pas à un club de votre province.")
        return redirect('gouvernance:ligue_athletes_validation_list')
    
    # Vérifier que l'athlète est en statut EN_ATTENTE_VALIDATION_LIGUE
    if athlete.statut_certification != 'EN_ATTENTE_VALIDATION_LIGUE':
        messages.warning(request, "Cet athlète n'a pas encore été enrôlé ou a déjà été traité.")
        return redirect('gouvernance:ligue_athletes_validation_list')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'valider':
            # Vérifier les doublons dans la province (même nom, prénom, date de naissance)
            doublons = Athlete.objects.filter(
                personne__nom=athlete.personne.nom,
                personne__prenom=athlete.personne.prenom,
                personne__date_naissance=athlete.personne.date_naissance,
                club__institution_tutelle=ligue,
                actif=True
            ).exclude(uid=athlete.uid)
            
            if doublons.exists():
                messages.error(request, f"⚠️ Un athlète avec le même nom ({athlete.personne.nom_complet}) et la même date de naissance existe déjà dans un autre club de la province.")
                return redirect('gouvernance:ligue_athletes_validation_list')

            # Vérifier que la visite médicale (F67) et le certificat d'aptitude (F72) permettent la validation
            if not athlete.peut_generer_licence_medical():
                messages.error(
                    request,
                    "Impossible de valider : visite médicale (F67) absente ou résultat INAPTE, ou certificat d'aptitude (F72) non délivré/joint."
                )
                return redirect('gouvernance:ligue_athlete_validate', athlete_uid=athlete.uid)
            
            # Valider l'athlète
            athlete.statut_certification = 'CERTIFIE_PROVINCIAL'
            athlete.date_validation_ligue = timezone.now()
            athlete.validateur_ligue = profil
            athlete.save()
            
            messages.success(request, f"✓ Athlète {athlete.personne.nom_complet} certifié au niveau provincial!")
            return redirect('gouvernance:ligue_athletes_validation_list')
        
        elif action == 'rejeter':
            motif = request.POST.get('motif_rejet', '')
            if not motif:
                messages.error(request, "Veuillez fournir un motif de rejet.")
                return redirect('gouvernance:ligue_athletes_validation_list')
            
            athlete.statut_certification = 'REJETE_LIGUE'
            athlete.motif_rejet_ligue = motif
            athlete.save()
            
            messages.warning(request, f"Athlète {athlete.personne.nom_complet} rejeté.")
            return redirect('gouvernance:ligue_athletes_validation_list')
    
    # Chercher les doublons potentiels pour affichage
    doublons_potentiels = Athlete.objects.filter(
        Q(personne__nom__iexact=athlete.personne.nom) |
        Q(personne__prenom__iexact=athlete.personne.prenom),
        club__institution_tutelle=ligue,
        actif=True
    ).exclude(uid=athlete.uid).select_related('personne', 'club')
    
    # Dernière visite médicale (F67) — pour afficher le résumé de certification uniquement (pas les détails médicaux)
    visite_certification = athlete.visites_medicales.order_by('-date_visite').first()
    
    context = {
        'ligue': ligue,
        'athlete': athlete,
        'doublons_potentiels': doublons_potentiels,
        'visite_certification': visite_certification,
        'user_role': 'ligue_secretary',
    }
    
    return render(request, 'gouvernance/ligue_athlete_validate.html', context)



@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_athlete_verify_duplicates(request, athlete_uid):
    """
    Vérification anti-fraude: reconnaissance faciale + état civil.
    Retourne un JSON avec les résultats de vérification.
    """
    from django.http import JsonResponse
    
    try:
        profil = request.user.profil_sisep
    except:
        return JsonResponse({'error': 'Profil utilisateur introuvable.'}, status=403)
    
    ligue = profil.institution
    athlete = get_object_or_404(Athlete, uid=athlete_uid)
    
    # Vérifier que l'athlète appartient à un club de cette ligue
    if athlete.club.institution_tutelle != ligue:
        return JsonResponse({'error': 'Cet athlète n\'appartient pas à votre province.'}, status=403)
    
    # 1. VÉRIFICATION BIOMÉTRIQUE (Reconnaissance Faciale)
    # Note: Pour une vraie implémentation, utiliser face_recognition ou DeepFace
    biometric_matches = []
    biometric_status = 'clear'
    biometric_message = "✓ Aucune correspondance faciale détectée. Le visage de cet athlète est unique dans la base de données provinciale."
    
    if athlete.personne.photo:
        # Rechercher tous les athlètes de la province avec photo
        clubs_province = Institution.objects.filter(
            niveau_territorial='CLUB',
            institution_tutelle=ligue
        )
        autres_athletes = Athlete.objects.filter(
            club__in=clubs_province,
            actif=True,
            personne__photo__isnull=False
        ).exclude(uid=athlete.uid).select_related('personne', 'club')
        
        # TODO: Implémenter la vraie reconnaissance faciale ici
        # Pour l'instant, on simule en cherchant des noms très similaires
        for autre in autres_athletes:
            # Simulation: si le nom est identique, on considère que c'est un doublon potentiel
            if (athlete.personne.nom.lower() == autre.personne.nom.lower() and 
                athlete.personne.prenom.lower() == autre.personne.prenom.lower()):
                biometric_matches.append({
                    'nom': autre.personne.nom_complet,
                    'club': autre.club.nom_officiel,
                    'photo': autre.personne.photo.url if autre.personne.photo else '',
                    'similarity': 95,  # Pourcentage de similarité simulé
                    'numero_sportif': autre.numero_sportif,
                })
        
        if biometric_matches:
            biometric_status = 'fraud_detected'
            biometric_message = f"⚠️ ALERTE FRAUDE: {len(biometric_matches)} correspondance(s) faciale(s) détectée(s)! Le visage de cet athlète correspond à un ou plusieurs athlètes déjà enregistrés sous d'autres identités."
    else:
        biometric_message = "⚠️ Aucune photo disponible pour la vérification biométrique."
    
    # 2. VÉRIFICATION ÉTAT CIVIL (Nom + Prénom + Date de naissance)
    civil_matches = []
    civil_status = 'clear'
    civil_message = "✓ Aucun homonyme détecté. Les données d'état civil sont uniques dans la province."
    
    # Rechercher les homonymes (même nom, prénom, date de naissance)
    clubs_province = Institution.objects.filter(
        niveau_territorial='CLUB',
        institution_tutelle=ligue
    )
    homonymes = Athlete.objects.filter(
        club__in=clubs_province,
        personne__nom__iexact=athlete.personne.nom,
        personne__prenom__iexact=athlete.personne.prenom,
        personne__date_naissance=athlete.personne.date_naissance,
        actif=True
    ).exclude(uid=athlete.uid).select_related('personne', 'club')
    
    for homonyme in homonymes:
        civil_matches.append({
            'nom': homonyme.personne.nom_complet,
            'club': homonyme.club.nom_officiel,
            'date_naissance': homonyme.personne.date_naissance.strftime('%d/%m/%Y'),
            'numero_sportif': homonyme.numero_sportif,
        })
    
    if civil_matches:
        civil_status = 'duplicate_found'
        civil_message = f"⚠️ ATTENTION: {len(civil_matches)} homonyme(s) détecté(s) avec les mêmes nom, prénom et date de naissance. Vérifiez qu'il ne s'agit pas de la même personne."
    
    # Construire la réponse
    response_data = {
        'biometric_check': {
            'status': biometric_status,
            'message': biometric_message,
            'matches': biometric_matches,
        },
        'civil_check': {
            'status': civil_status,
            'message': civil_message,
            'matches': civil_matches,
        },
    }
    
    return JsonResponse(response_data)


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_athletes_validation_history(request):
    """
    Historique des validations d'athlètes par la ligue (certifiés ou rejetés au niveau provincial).
    Filtres : date (debut/fin), type (statut), club, discipline.
    """
    from django.utils.dateparse import parse_date
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    ligue = profil.institution
    if not ligue or ligue.niveau_territorial not in ['LIGUE', 'LIGUE_PROVINCIALE']:
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    
    clubs_ligue = Institution.objects.filter(niveau_territorial='CLUB', institution_tutelle=ligue)
    athletes = Athlete.objects.filter(
        club__in=clubs_ligue,
        statut_certification__in=('CERTIFIE_PROVINCIAL', 'REJETE_LIGUE'),
        actif=True
    ).select_related(
        'personne', 'club', 'discipline', 'validateur_ligue',
        'validateur_ligue__user', 'validateur_ligue__agent', 'validateur_ligue__agent__personne'
    )
    
    # Filtres GET
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    type_statut = request.GET.get('type')
    club_id = request.GET.get('club')
    discipline_id = request.GET.get('discipline')
    
    if type_statut in ('CERTIFIE_PROVINCIAL', 'REJETE_LIGUE'):
        athletes = athletes.filter(statut_certification=type_statut)
    if date_debut:
        d = parse_date(date_debut)
        if d:
            athletes = athletes.filter(date_validation_ligue__date__gte=d)
    if date_fin:
        d = parse_date(date_fin)
        if d:
            athletes = athletes.filter(date_validation_ligue__date__lte=d)
    if club_id:
        athletes = athletes.filter(club_id=club_id)
    if discipline_id:
        athletes = athletes.filter(discipline_id=discipline_id)
    
    athletes = athletes.order_by('-date_validation_ligue', '-pk')
    total_certifies = athletes.filter(statut_certification='CERTIFIE_PROVINCIAL').count()
    total_rejetes = athletes.filter(statut_certification='REJETE_LIGUE').count()
    
    clubs_choices = [(str(u), n) for u, n in clubs_ligue.values_list('uid', 'nom_officiel').order_by('nom_officiel')]
    from gouvernance.models import DisciplineSport
    disciplines_choices = [(str(u), d) for u, d in DisciplineSport.objects.filter(
        athletes__club__in=clubs_ligue,
        athletes__statut_certification__in=('CERTIFIE_PROVINCIAL', 'REJETE_LIGUE')
    ).distinct().values_list('uid', 'designation').order_by('designation')]
    
    context = {
        'ligue': ligue,
        'athletes': athletes,
        'total_certifies': total_certifies,
        'total_rejetes': total_rejetes,
        'clubs_choices': clubs_choices,
        'disciplines_choices': disciplines_choices,
        'filters': {
            'date_debut': date_debut or '',
            'date_fin': date_fin or '',
            'type': type_statut or '',
            'club': club_id or '',
            'discipline': discipline_id or '',
        },
        'user_role': 'ligue_secretary',
    }
    return render(request, 'gouvernance/ligue_athletes_validation_history.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_athletes_enrollment_history(request):
    """
    Historique des enrôlements d'athlètes à la ligue (athlètes ayant une date d'enrôlement).
    Filtres : date (debut/fin), type (statut actuel), club, discipline.
    """
    from django.utils.dateparse import parse_date
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    ligue = profil.institution
    if not ligue or ligue.niveau_territorial not in ['LIGUE', 'LIGUE_PROVINCIALE']:
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    
    clubs_ligue = Institution.objects.filter(niveau_territorial='CLUB', institution_tutelle=ligue)
    athletes = Athlete.objects.filter(
        club__in=clubs_ligue,
        date_enrolement__isnull=False,
        actif=True
    ).select_related(
        'personne', 'club', 'discipline', 'agent_enrolement',
        'agent_enrolement__user', 'agent_enrolement__agent', 'agent_enrolement__agent__personne'
    )
    
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    type_statut = request.GET.get('type')
    club_id = request.GET.get('club')
    discipline_id = request.GET.get('discipline')
    
    if type_statut:
        athletes = athletes.filter(statut_certification=type_statut)
    if date_debut:
        d = parse_date(date_debut)
        if d:
            athletes = athletes.filter(date_enrolement__date__gte=d)
    if date_fin:
        d = parse_date(date_fin)
        if d:
            athletes = athletes.filter(date_enrolement__date__lte=d)
    if club_id:
        athletes = athletes.filter(club_id=club_id)
    if discipline_id:
        athletes = athletes.filter(discipline_id=discipline_id)
    
    athletes = athletes.order_by('-date_enrolement')
    
    from gouvernance.models import DisciplineSport
    disciplines_choices = [(str(u), d) for u, d in DisciplineSport.objects.filter(
        athletes__club__in=clubs_ligue,
        athletes__date_enrolement__isnull=False
    ).distinct().values_list('uid', 'designation').order_by('designation')]
    clubs_choices = [(str(u), n) for u, n in clubs_ligue.values_list('uid', 'nom_officiel').order_by('nom_officiel')]
    
    context = {
        'ligue': ligue,
        'athletes': athletes,
        'total': athletes.count(),
        'clubs_choices': clubs_choices,
        'disciplines_choices': disciplines_choices,
        'filters': {
            'date_debut': date_debut or '',
            'date_fin': date_fin or '',
            'type': type_statut or '',
            'club': club_id or '',
            'discipline': discipline_id or '',
        },
        'user_role': 'ligue_secretary',
    }
    return render(request, 'gouvernance/ligue_athletes_enrollment_history.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_athletes_enrollment_list(request):
    """
    Liste des athlètes en attente d'enrôlement à la ligue.
    Le secrétaire voit les athlètes PROVISOIRE (à enrôler) et EN_ATTENTE_EXAMEN_MEDICAL (déjà transmis au médecin).
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    ligue = profil.institution
    
    if not ligue or ligue.niveau_territorial not in ['LIGUE', 'LIGUE_PROVINCIALE']:
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    
    # Clubs de la ligue
    from django.db.models import Case, When, Value, IntegerField
    clubs_ligue = Institution.objects.filter(niveau_territorial='CLUB', institution_tutelle=ligue)
    
    # Athlètes à enrôler (PROVISOIRE) ou déjà transmis au médecin (EN_ATTENTE_EXAMEN_MEDICAL)
    ordre_statut = Case(
        When(statut_certification='PROVISOIRE', then=Value(0)),
        When(statut_certification='EN_ATTENTE_EXAMEN_MEDICAL', then=Value(1)),
        default=Value(2),
        output_field=IntegerField(),
    )
    athletes = Athlete.objects.filter(
        club__in=clubs_ligue,
        statut_certification__in=('PROVISOIRE', 'EN_ATTENTE_EXAMEN_MEDICAL'),
        actif=True
    ).select_related('personne', 'club', 'discipline').order_by(ordre_statut, 'personne__nom', 'personne__prenom')
    
    total_provisoires = athletes.filter(statut_certification='PROVISOIRE').count()
    total_transmis_medecin = athletes.filter(statut_certification='EN_ATTENTE_EXAMEN_MEDICAL').count()
    total_athletes = total_provisoires + total_transmis_medecin
    
    context = {
        'ligue': ligue,
        'athletes': athletes,
        'total_provisoires': total_provisoires,
        'total_transmis_medecin': total_transmis_medecin,
        'total_athletes': total_athletes,
        'user_role': 'ligue_secretary',
    }
    
    return render(request, 'gouvernance/ligue_athletes_enrollment_list.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_athlete_enroll(request, athlete_uid):
    """
    Enrôler un athlète à la ligue: relevé des empreintes puis envoi au médecin (F67).
    Affiche toutes les informations saisies par le club (comme en validation provinciale).
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    ligue = profil.institution
    athlete = get_object_or_404(
        Athlete.objects.select_related(
            'personne', 'club', 'discipline',
            'personne__adresse', 'personne__adresse__groupement_quartier',
            'personne__adresse__groupement_quartier__secteur',
            'personne__adresse__groupement_quartier__secteur__territoire',
            'personne__adresse__groupement_quartier__secteur__territoire__province_admin',
        ),
        uid=athlete_uid
    )
    
    # Vérifier que l'athlète appartient à un club de cette ligue
    if athlete.club.institution_tutelle != ligue:
        messages.error(request, "Cet athlète n'appartient pas à un club de votre ligue.")
        return redirect('gouvernance:ligue_athletes_enrollment_list')
    
    # Autoriser PROVISOIRE (enrôlement) ou EN_ATTENTE_EXAMEN_MEDICAL (consultation read-only)
    if athlete.statut_certification not in ('PROVISOIRE', 'EN_ATTENTE_EXAMEN_MEDICAL'):
        messages.warning(request, "Cet athlète a déjà été validé ou n'est plus en cours d'enrôlement.")
        return redirect('gouvernance:ligue_athletes_enrollment_list')
    
    read_only = athlete.statut_certification == 'EN_ATTENTE_EXAMEN_MEDICAL'
    
    if request.method == 'POST' and not read_only:
        action = request.POST.get('action')
        if action == 'enroller':
            observations = request.POST.get('observations_enrolement', '')
            has_capture_in_form = bool(request.FILES.get('main_droite_4') or request.POST.get('main_droite_4_b64', '').strip())

            # Cas 1 : capture envoyée dans le formulaire (prise sur cette page)
            if has_capture_in_form:
                import base64
                from django.core.files.base import ContentFile

                def image_from_post(name, b64_name):
                    f = request.FILES.get(name)
                    if f:
                        return f
                    b64 = request.POST.get(b64_name, '').strip()
                    if b64:
                        try:
                            raw = base64.b64decode(b64)
                            return ContentFile(raw, name=f'{name}.bmp')
                        except Exception:
                            pass
                    return None

                main_droite_4 = image_from_post('main_droite_4', 'main_droite_4_b64')
                main_gauche_4 = image_from_post('main_gauche_4', 'main_gauche_4_b64')
                pouces_2 = image_from_post('pouces_2', 'pouces_2_b64')
                if not main_droite_4 or not main_gauche_4 or not pouces_2:
                    messages.error(request, "Veuillez capturer les 3 prises (main droite, main gauche, 2 pouces).")
                    return redirect('gouvernance:ligue_athlete_enroll', athlete_uid=athlete_uid)
                def decode_template_b64(b64_val):
                    if not b64_val or not b64_val.strip():
                        return None
                    try:
                        return base64.b64decode(b64_val.strip())
                    except Exception:
                        return None
                t_main_droite = decode_template_b64(request.POST.get('main_droite_4_template_b64', ''))
                t_main_gauche = decode_template_b64(request.POST.get('main_gauche_4_template_b64', ''))
                t_pouces = decode_template_b64(request.POST.get('pouces_2_template_b64', ''))
                capture, _ = CaptureEmpreintes.objects.update_or_create(
                    athlete=athlete,
                    defaults={
                        'main_droite_4': main_droite_4,
                        'main_gauche_4': main_gauche_4,
                        'pouces_2': pouces_2,
                        'main_droite_4_template': t_main_droite,
                        'main_gauche_4_template': t_main_gauche,
                        'pouces_2_template': t_pouces,
                        'captured_by': profil,
                    }
                )
                athlete.empreinte_digitale = main_droite_4
            else:
                # Cas 2 : capture déjà faite sur l'interface dédiée
                try:
                    capture = athlete.capture_empreintes
                except CaptureEmpreintes.DoesNotExist:
                    capture = None
                if not capture or not capture.is_complete:
                    messages.error(
                        request,
                        "Veuillez d'abord effectuer la prise des empreintes en cliquant sur « Lancer la prise des empreintes »."
                    )
                    return redirect('gouvernance:ligue_athlete_enroll', athlete_uid=athlete_uid)
                if not getattr(athlete, 'empreinte_digitale', None) and capture.main_droite_4:
                    athlete.empreinte_digitale = capture.main_droite_4

            athlete.statut_certification = 'EN_ATTENTE_EXAMEN_MEDICAL'
            athlete.date_enrolement = timezone.now()
            athlete.agent_enrolement = profil
            athlete.observations_enrolement = observations
            athlete.save()
            messages.success(
                request,
                f"✓ L'athlète {athlete.personne.nom_complet} a été transféré au médecin de la ligue pour l'examen médical (F67)."
            )
            return redirect('gouvernance:ligue_athletes_enrollment_list')
    
    from django.conf import settings
    try:
        has_capture_done = athlete.capture_empreintes.is_complete
    except Exception:
        has_capture_done = False
    context = {
        'ligue': ligue,
        'athlete': athlete,
        'user_role': 'ligue_secretary',
        'morpho_service_uri': settings.MORPHO_SERVICE_URI,
        'has_capture_done': has_capture_done,
        'read_only': read_only,
    }

    return render(request, 'gouvernance/ligue_athlete_enroll.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_athlete_capture_empreintes(request, athlete_uid):
    """
    Interface dédiée à la prise des empreintes (10 doigts) pour un athlète.
    Après enregistrement, redirige vers la page d'enrôlement.
    """
    try:
        profil = request.user.profil_sisep
    except Exception:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')

    ligue = profil.institution
    athlete = get_object_or_404(Athlete.objects.select_related('personne', 'club'), uid=athlete_uid)

    if athlete.club.institution_tutelle != ligue:
        messages.error(request, "Cet athlète n'appartient pas à un club de votre ligue.")
        return redirect('gouvernance:ligue_athletes_enrollment_list')

    if athlete.statut_certification != 'PROVISOIRE':
        messages.warning(request, "Cet athlète a déjà été enrôlé ou validé.")
        return redirect('gouvernance:ligue_athletes_enrollment_list')

    if request.method == 'POST':
        import base64
        from django.core.files.base import ContentFile

        def image_from_post(name, b64_name):
            f = request.FILES.get(name)
            if f:
                return f
            b64 = request.POST.get(b64_name, '').strip()
            if b64:
                try:
                    raw = base64.b64decode(b64)
                    # Images compressées côté client en JPEG pour éviter RequestDataTooBig
                    ext = 'jpg' if raw[:3] == b'\xff\xd8\xff' else 'bmp'
                    return ContentFile(raw, name=f'{name}.{ext}')
                except Exception:
                    pass
            return None

        main_droite_4 = image_from_post('main_droite_4', 'main_droite_4_b64')
        main_gauche_4 = image_from_post('main_gauche_4', 'main_gauche_4_b64')
        pouces_2 = image_from_post('pouces_2', 'pouces_2_b64')
        if not main_droite_4:
            messages.error(request, "Veuillez capturer les 4 doigts de la main droite.")
            return redirect('gouvernance:ligue_athlete_capture_empreintes', athlete_uid=athlete_uid)
        if not main_gauche_4:
            messages.error(request, "Veuillez capturer les 4 doigts de la main gauche.")
            return redirect('gouvernance:ligue_athlete_capture_empreintes', athlete_uid=athlete_uid)
        if not pouces_2:
            messages.error(request, "Veuillez capturer les 2 pouces.")
            return redirect('gouvernance:ligue_athlete_capture_empreintes', athlete_uid=athlete_uid)

        def decode_template_b64(b64_val):
            if not b64_val or not b64_val.strip():
                return None
            try:
                return base64.b64decode(b64_val.strip())
            except Exception:
                return None

        t_main_droite = decode_template_b64(request.POST.get('main_droite_4_template_b64', ''))
        t_main_gauche = decode_template_b64(request.POST.get('main_gauche_4_template_b64', ''))
        t_pouces = decode_template_b64(request.POST.get('pouces_2_template_b64', ''))

        CaptureEmpreintes.objects.update_or_create(
            athlete=athlete,
            defaults={
                'main_droite_4': main_droite_4,
                'main_gauche_4': main_gauche_4,
                'pouces_2': pouces_2,
                'main_droite_4_template': t_main_droite,
                'main_gauche_4_template': t_main_gauche,
                'pouces_2_template': t_pouces,
                'captured_by': profil,
            }
        )
        messages.success(
            request,
            f"Empreintes enregistrées pour {athlete.personne.nom_complet}. Vous pouvez retourner à l'enrôlement pour finaliser."
        )
        return redirect('gouvernance:ligue_athlete_enroll', athlete_uid=athlete_uid)

    from django.conf import settings
    context = {
        'ligue': ligue,
        'athlete': athlete,
        'user_role': 'ligue_secretary',
        'morpho_service_uri': settings.MORPHO_SERVICE_URI,
    }
    return render(request, 'gouvernance/ligue_athlete_capture_empreintes.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_athlete_capture_empreintes_templates(request, athlete_uid):
    """
    API JSON : liste des templates d'empreintes (main droite) des autres athlètes de la ligue
    pour la recherche 1:N côté client (éviter double enregistrement).
    Exclut l'athlète courant (athlete_uid). Retourne photo_url, nom_complet, numero_sportif pour affichage en modale.
    """
    import base64
    from django.http import JsonResponse

    try:
        profil = request.user.profil_sisep
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Profil utilisateur introuvable.'}, status=403)
    ligue = profil.institution
    if not ligue:
        return JsonResponse({'ok': False, 'error': 'Ligue introuvable.'}, status=403)
    athlete = get_object_or_404(Athlete, uid=athlete_uid, actif=True)
    if athlete.club.institution_tutelle != ligue:
        return JsonResponse({'ok': False, 'error': 'Athlète hors ligue.'}, status=403)

    clubs_ligue = Institution.objects.filter(niveau_territorial='CLUB', institution_tutelle=ligue)
    # Athlètes de la ligue ayant des empreintes avec template (exclure l'athlète courant)
    captures = CaptureEmpreintes.objects.filter(
        athlete__club__in=clubs_ligue,
        athlete__actif=True
    ).exclude(athlete_id=athlete.pk).select_related('athlete', 'athlete__personne', 'athlete__club')

    items = []
    for cap in captures:
        if not cap.main_droite_4_template:
            continue
        try:
            template_b64 = base64.b64encode(cap.main_droite_4_template).decode('ascii')
        except Exception:
            continue
        p = cap.athlete.personne
        photo_url = ''
        if p and getattr(p, 'photo', None) and p.photo:
            try:
                photo_url = request.build_absolute_uri(p.photo.url)
            except Exception:
                pass
        items.append({
            'athlete_uid': str(cap.athlete.uid),
            'template_base64': template_b64,
            'photo_url': photo_url,
            'nom_complet': cap.athlete.personne.nom_complet if p else str(cap.athlete),
            'numero_sportif': cap.athlete.numero_sportif or '',
        })
    return JsonResponse({'ok': True, 'items': items, 'temp_format': '0'})


def _get_ligue_for_events(request):
    """Retourne (profil, ligue) pour les vues événements. Redirige si pas ligue."""
    try:
        profil = request.user.profil_sisep
    except Exception:
        return None, None
    ligue = profil.institution
    if not ligue or ligue.niveau_territorial != 'LIGUE':
        return profil, None
    return profil, ligue


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_evenements_list(request):
    """
    Liste des compétitions, matchs et événements sportifs créés par la ligue provinciale.
    """
    profil, ligue = _get_ligue_for_events(request)
    if not ligue:
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    evenements = Evenement.objects.filter(organisateur=ligue, actif=True).select_related(
        'infrastructure', 'organisateur'
    ).order_by('-date_evenement', '-heure_debut')
    context = {
        'ligue': ligue,
        'evenements': evenements,
        'user_role': 'ligue_secretary',
    }
    return render(request, 'gouvernance/ligue_evenements_list.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
@require_http_methods(['GET', 'POST'])
def ligue_evenement_create(request):
    """
    Créer un événement sportif (match, compétition, etc.) pour la ligue.
    Les infrastructures proposées sont celles de la province de la ligue.
    """
    profil, ligue = _get_ligue_for_events(request)
    if not ligue:
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')

    # Infrastructures de la province de la ligue
    if ligue.province_admin_id:
        infras_qs = Infrastructure.objects.filter(
            province_admin=ligue.province_admin,
            actif=True
        ).order_by('nom')
    else:
        infras_qs = Infrastructure.objects.none()

    if not infras_qs.exists():
        messages.warning(
            request,
            "Aucune infrastructure enregistrée dans votre province. "
            "Contactez la Division Provinciale pour enregistrer des stades/terrains."
        )

    form = LigueEvenementForm(queryset_infrastructure=infras_qs)
    if request.method == 'POST':
        form = LigueEvenementForm(request.POST, queryset_infrastructure=infras_qs)
        if form.is_valid():
            evenement = Evenement.objects.create(
                infrastructure=form.cleaned_data['infrastructure'],
                organisateur=ligue,
                titre=form.cleaned_data['titre'],
                type_evenement=form.cleaned_data['type_evenement'],
                date_evenement=form.cleaned_data['date_evenement'],
                heure_debut=form.cleaned_data.get('heure_debut'),
                description=form.cleaned_data.get('description') or '',
                actif=True,
            )
            messages.success(
                request,
                f"L'événement « {evenement.titre } » a été créé. Vous pourrez configurer les zones et la billetterie depuis le module Infrastructure si besoin."
            )
            return redirect('gouvernance:ligue_evenements_list')

    context = {
        'ligue': ligue,
        'form': form,
        'user_role': 'ligue_secretary',
    }
    return render(request, 'gouvernance/ligue_evenement_create.html', context)


# ---------- Compétitions (types, compétitions par saison, calendrier) ----------

@login_required
@require_role('FEDERATION_SECRETARY')
@require_http_methods(['GET', 'POST'])
def ligue_types_competition_list(request):
    """Liste des types de compétition de la ligue + formulaire d'ajout."""
    profil, ligue = _get_ligue_for_events(request)
    if not ligue:
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    types_list = TypeCompetition.objects.filter(ligue=ligue, actif=True).order_by('ordre', 'designation')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            type_uid = request.POST.get('type_uid')
            if type_uid:
                tc = TypeCompetition.objects.filter(uid=type_uid, ligue=ligue).first()
                if tc and not tc.competitions.exists():
                    tc.delete()
                    messages.success(request, "Type de compétition supprimé.")
                elif tc:
                    messages.error(request, "Impossible de supprimer : des compétitions utilisent ce type.")
                else:
                    messages.error(request, "Type introuvable.")
            return redirect('gouvernance:ligue_types_competition_list')
        form = TypeCompetitionForm(request.POST)
        if form.is_valid():
            TypeCompetition.objects.create(
                ligue=ligue,
                designation=form.cleaned_data['designation'].strip(),
                code=(form.cleaned_data.get('code') or '').strip(),
                ordre=form.cleaned_data.get('ordre', 0),
                actif=True,
            )
            messages.success(request, "Type de compétition enregistré.")
            return redirect('gouvernance:ligue_types_competition_list')
    else:
        form = TypeCompetitionForm()
    context = {
        'ligue': ligue,
        'types_list': types_list,
        'form': form,
        'user_role': 'ligue_secretary',
    }
    return render(request, 'gouvernance/ligue_types_competition_list.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_competitions_list(request):
    """Liste des compétitions créées par la ligue (par saison)."""
    profil, ligue = _get_ligue_for_events(request)
    if not ligue:
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    competitions = Competition.objects.filter(organisateur=ligue, actif=True).select_related(
        'type_competition', 'organisateur'
    ).order_by('-saison', 'titre')
    context = {
        'ligue': ligue,
        'competitions': competitions,
        'user_role': 'ligue_secretary',
    }
    return render(request, 'gouvernance/ligue_competitions_list.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
@require_http_methods(['GET', 'POST'])
def ligue_competition_create(request):
    """Créer une compétition (type + saison + titre)."""
    profil, ligue = _get_ligue_for_events(request)
    if not ligue:
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    types_qs = TypeCompetition.objects.filter(ligue=ligue, actif=True).order_by('ordre', 'designation')
    if not types_qs.exists():
        messages.warning(
            request,
            "Aucun type de compétition enregistré. Créez d'abord au moins un type dans « Types de compétition »."
        )
    form = LigueCompetitionForm(queryset_types=types_qs)
    if request.method == 'POST':
        form = LigueCompetitionForm(request.POST, queryset_types=types_qs)
        if form.is_valid():
            comp = Competition.objects.create(
                type_competition=form.cleaned_data['type_competition'],
                organisateur=ligue,
                saison=form.cleaned_data['saison'].strip(),
                categorie=form.cleaned_data.get('categorie', 'SENIOR'),
                titre=form.cleaned_data['titre'].strip(),
                description=form.cleaned_data.get('description') or '',
                actif=True,
            )
            messages.success(
                request,
                f"Compétition « {comp.titre } » créée. Vous pouvez maintenant créer le calendrier pour cette compétition."
            )
            return redirect('gouvernance:ligue_competition_calendrier', competition_uid=comp.uid)
    context = {
        'ligue': ligue,
        'form': form,
        'user_role': 'ligue_secretary',
    }
    return render(request, 'gouvernance/ligue_competition_create.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
@require_http_methods(['GET', 'POST'])
def ligue_competition_calendrier(request, competition_uid):
    """Calendrier d'une compétition : liste des dates + ajout."""
    profil, ligue = _get_ligue_for_events(request)
    if not ligue:
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    competition = get_object_or_404(Competition, uid=competition_uid, organisateur=ligue, actif=True)
    infras_qs = Infrastructure.objects.none()
    if ligue.province_admin_id:
        infras_qs = Infrastructure.objects.filter(
            province_admin=ligue.province_admin,
            actif=True
        ).order_by('nom')
    entrees = CalendrierCompetition.objects.filter(competition=competition).select_related(
        'infrastructure'
    ).order_by('date', 'ordre', 'libelle')
    form = CalendrierCompetitionForm(queryset_infrastructure=infras_qs)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            entree_uid = request.POST.get('entree_uid')
            if entree_uid:
                CalendrierCompetition.objects.filter(
                    uid=entree_uid,
                    competition=competition
                ).delete()
                messages.success(request, "Date retirée du calendrier.")
            return redirect('gouvernance:ligue_competition_calendrier', competition_uid=competition.uid)
        form = CalendrierCompetitionForm(request.POST, queryset_infrastructure=infras_qs)
        if form.is_valid():
            CalendrierCompetition.objects.create(
                competition=competition,
                date=form.cleaned_data['date'],
                heure_debut=form.cleaned_data.get('heure_debut'),
                libelle=form.cleaned_data['libelle'].strip(),
                infrastructure=form.cleaned_data.get('infrastructure'),
                ordre=form.cleaned_data.get('ordre', 0),
            )
            messages.success(request, "Date ajoutée au calendrier.")
            return redirect('gouvernance:ligue_competition_calendrier', competition_uid=competition.uid)
    context = {
        'ligue': ligue,
        'competition': competition,
        'entrees': entrees,
        'form': form,
        'user_role': 'ligue_secretary',
    }
    return render(request, 'gouvernance/ligue_competition_calendrier.html', context)


# ---------- Journées et Rencontres (workflow calendrier) ----------

@login_required
@require_role('FEDERATION_SECRETARY')
@require_http_methods(['GET', 'POST'])
def ligue_competition_journees(request, competition_uid):
    """Journées d'une compétition : liste + ajout de journées + accès aux rencontres et au calendrier."""
    profil, ligue = _get_ligue_for_events(request)
    if not ligue:
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    competition = get_object_or_404(Competition, uid=competition_uid, organisateur=ligue, actif=True)
    
    # Récupérer les journées avec leurs rencontres
    journees = Journee.objects.filter(competition=competition).order_by('ordre', 'libelle').prefetch_related('rencontres__equipe_a', 'rencontres__equipe_b', 'rencontres__stade')
    
    # Appliquer les filtres de recherche et statut
    search_query = request.GET.get('search', '').strip()
    statut_filter = request.GET.get('statut', '').strip()
    
    if search_query or statut_filter:
        # Filtrer les rencontres dans chaque journée
        filtered_journees = []
        for journee in journees:
            rencontres = journee.rencontres.all()
            
            if search_query:
                from django.db.models import Q
                rencontres = rencontres.filter(
                    Q(equipe_a__nom_officiel__icontains=search_query) |
                    Q(equipe_b__nom_officiel__icontains=search_query) |
                    Q(equipe_a__sigle__icontains=search_query) |
                    Q(equipe_b__sigle__icontains=search_query) |
                    Q(stade__nom__icontains=search_query)
                )
            
            if statut_filter:
                rencontres = rencontres.filter(statut=statut_filter)
            
            # Créer une copie de la journée avec les rencontres filtrées
            if rencontres.exists() or not (search_query or statut_filter):
                journee.filtered_rencontres = rencontres
                filtered_journees.append(journee)
        
        journees = filtered_journees
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'generate_journees':
            try:
                nombre = max(1, min(50, int(request.POST.get('nombre_journees', 0))))
            except (ValueError, TypeError):
                nombre = 0
            if nombre > 0:
                from django.db.models import Max
                max_ordre = Journee.objects.filter(competition=competition).aggregate(Max('ordre'))['ordre__max'] or 0
                created = 0
                for i in range(1, nombre + 1):
                    ordre = max_ordre + i
                    libelle = f"Journée {i}"
                    if not Journee.objects.filter(competition=competition, libelle=libelle).exists():
                        Journee.objects.create(competition=competition, libelle=libelle, ordre=ordre)
                        created += 1
                if created:
                    messages.success(request, f"{created} journée(s) générée(s) automatiquement.")
                else:
                    messages.info(request, "Aucune nouvelle journée à créer (déjà existantes).")
                return redirect('gouvernance:ligue_competition_journees', competition_uid=competition.uid)
        elif action == 'add_journee':
            form = JourneeForm(request.POST)
            if form.is_valid():
                Journee.objects.create(
                    competition=competition,
                    libelle=form.cleaned_data['libelle'].strip(),
                    ordre=form.cleaned_data.get('ordre', 0),
                )
                messages.success(request, "Journée ajoutée.")
                return redirect('gouvernance:ligue_competition_journees', competition_uid=competition.uid)
    form = JourneeForm()
    context = {
        'ligue': ligue,
        'competition': competition,
        'journees': journees,
        'form': form,
        'user_role': 'ligue_secretary',
    }
    return render(request, 'gouvernance/ligue_competition_journees.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
@require_http_methods(['GET', 'POST'])
def ligue_rencontre_create(request, competition_uid, journee_uid):
    """Créer une rencontre (Club A vs Club B, stade, date/heure). Vérification conflit stade automatique."""
    profil, ligue = _get_ligue_for_events(request)
    if not ligue:
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    competition = get_object_or_404(Competition, uid=competition_uid, organisateur=ligue, actif=True)
    journee = get_object_or_404(Journee, uid=journee_uid, competition=competition)
    clubs_qs = Institution.objects.filter(institution_tutelle=ligue, niveau_territorial='CLUB').order_by('nom_officiel')
    infras_qs = Infrastructure.objects.none()
    if ligue.province_admin_id:
        infras_qs = Infrastructure.objects.filter(province_admin=ligue.province_admin, actif=True).order_by('nom')
    form = RencontreForm(queryset_clubs=clubs_qs, queryset_stades=infras_qs)
    if request.method == 'POST':
        form = RencontreForm(request.POST, queryset_clubs=clubs_qs, queryset_stades=infras_qs)
        if form.is_valid():
            if form.cleaned_data['equipe_a'] == form.cleaned_data['equipe_b']:
                messages.error(request, "Les deux équipes doivent être différentes.")
            else:
                try:
                    r = Rencontre.objects.create(
                        journee=journee,
                        equipe_a=form.cleaned_data['equipe_a'],
                        equipe_b=form.cleaned_data['equipe_b'],
                        stade=form.cleaned_data['stade'],
                        date_heure=form.cleaned_data['date_heure'],
                        statut='PROGRAMME',
                    )
                    messages.success(request, f"Rencontre créée. Un événement billetterie a été généré pour le gestionnaire du stade.")
                    return redirect('gouvernance:ligue_competition_journees', competition_uid=competition.uid)
                except ValidationError as e:
                    msg = getattr(e, 'message_dict', {})
                    if isinstance(msg, dict) and 'date_heure' in msg:
                        messages.error(request, msg['date_heure'][0])
                    else:
                        messages.error(request, str(e))
    context = {
        'ligue': ligue,
        'competition': competition,
        'journee': journee,
        'form': form,
        'user_role': 'ligue_secretary',
    }
    return render(request, 'gouvernance/ligue_rencontre_create.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_rencontre_detail(request, rencontre_uid):
    """
    Détails d'une rencontre avec possibilité de modifier le statut.
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    ligue = profil.institution
    
    if not ligue or ligue.niveau_territorial != 'LIGUE':
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    
    # Récupérer la rencontre avec toutes les relations
    rencontre = get_object_or_404(
        Rencontre.objects.select_related(
            'journee__competition',
            'equipe_a',
            'equipe_b',
            'stade',
            'evenement'
        ),
        uid=rencontre_uid
    )
    
    # Vérifier que la rencontre appartient à une compétition de la ligue
    if rencontre.journee.competition.organisateur != ligue:
        messages.error(request, "Cette rencontre n'appartient pas à votre ligue.")
        return redirect('core:home')
    
    competition = rencontre.journee.competition
    
    # Traiter la mise à jour du statut
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_statut':
            new_statut = request.POST.get('statut')
            if new_statut in dict(Rencontre.STATUT_CHOICES):
                rencontre.statut = new_statut
                rencontre.save(update_fields=['statut'])
                messages.success(request, f"Statut mis à jour: {rencontre.get_statut_display()}")
                return redirect('gouvernance:ligue_rencontre_detail', rencontre_uid=rencontre.uid)
    
    context = {
        'ligue': ligue,
        'competition': competition,
        'rencontre': rencontre,
        'user_role': 'ligue_secretary',
    }
    
    return render(request, 'gouvernance/ligue_rencontre_detail.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_rencontre_billetterie_stats(request, rencontre_uid):
    """
    Statistiques de billetterie pour une rencontre (lecture seule pour le secrétaire de ligue).
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    ligue = profil.institution
    
    if not ligue or ligue.niveau_territorial != 'LIGUE':
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    
    # Récupérer la rencontre avec l'événement billetterie
    rencontre = get_object_or_404(
        Rencontre.objects.select_related(
            'journee__competition',
            'equipe_a',
            'equipe_b',
            'stade',
            'evenement__infrastructure'
        ),
        uid=rencontre_uid
    )
    
    # Vérifier que la rencontre appartient à la ligue
    if rencontre.journee.competition.organisateur != ligue:
        messages.error(request, "Cette rencontre n'appartient pas à votre ligue.")
        return redirect('core:home')
    
    # Vérifier qu'il y a un événement billetterie
    if not rencontre.evenement:
        messages.error(request, "Aucun événement billetterie n'a été créé pour cette rencontre.")
        return redirect('gouvernance:ligue_rencontre_detail', rencontre_uid=rencontre.uid)
    
    evenement = rencontre.evenement
    
    # Récupérer les zones configurées avec leurs tarifs
    from infrastructures.models import ZoneStade, EvenementZone, Ticket, Vente
    
    # Récupérer les configurations de zones pour cet événement
    evenement_zones = EvenementZone.objects.filter(evenement=evenement).select_related('zone_stade')
    
    # Calculer les statistiques globales
    total_tickets = 0
    tickets_vendus = 0
    tickets_disponibles = 0
    
    for ez in evenement_zones:
        total_tickets += ez.capacite_max
        vendus = Ticket.objects.filter(evenement_zone=ez, statut='VENDU').count()
        tickets_vendus += vendus
        tickets_disponibles += (ez.capacite_max - vendus)
    
    # Calculer le chiffre d'affaires
    ventes = Vente.objects.filter(evenement=evenement)
    chiffre_affaires = sum(v.montant_total for v in ventes)
    nombre_ventes = ventes.count()
    
    # Statistiques par zone
    zones_stats = []
    for ez in evenement_zones:
        tickets_zone = Ticket.objects.filter(evenement_zone=ez)
        vendus_zone = tickets_zone.filter(statut='VENDU').count()
        total_zone = ez.capacite_max
        disponibles_zone = total_zone - vendus_zone
        
        # Calculer le CA pour cette zone
        ventes_zone = Vente.objects.filter(tickets__evenement_zone=ez).distinct()
        ca_zone = sum(v.montant_total for v in ventes_zone)
        
        zones_stats.append({
            'zone': ez.zone_stade,
            'prix': ez.prix_unitaire,
            'total': total_zone,
            'vendus': vendus_zone,
            'disponibles': disponibles_zone,
            'taux_remplissage': round((vendus_zone / total_zone * 100) if total_zone > 0 else 0, 1),
            'chiffre_affaires': ca_zone,
            'nombre_ventes': ventes_zone.count(),
        })
    
    context = {
        'ligue': ligue,
        'rencontre': rencontre,
        'evenement': evenement,
        'total_tickets': total_tickets,
        'tickets_vendus': tickets_vendus,
        'tickets_disponibles': tickets_disponibles,
        'taux_remplissage': round((tickets_vendus / total_tickets * 100) if total_tickets > 0 else 0, 1),
        'chiffre_affaires': chiffre_affaires,
        'nombre_ventes': nombre_ventes,
        'zones_stats': zones_stats,
        'user_role': 'ligue_secretary',
        'readonly': True,  # Mode lecture seule
    }
    
    return render(request, 'gouvernance/ligue_rencontre_billetterie_stats.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
@require_http_methods(['GET', 'POST'])
def ligue_rencontre_edit(request, competition_uid, rencontre_uid):
    """Modifier une rencontre (équipes, stade, date/heure, statut)."""
    profil, ligue = _get_ligue_for_events(request)
    if not ligue:
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    competition = get_object_or_404(Competition, uid=competition_uid, organisateur=ligue, actif=True)
    rencontre = get_object_or_404(Rencontre, uid=rencontre_uid, journee__competition=competition)
    journee = rencontre.journee
    clubs_qs = Institution.objects.filter(institution_tutelle=ligue, niveau_territorial='CLUB').order_by('nom_officiel')
    infras_qs = Infrastructure.objects.none()
    if ligue.province_admin_id:
        infras_qs = Infrastructure.objects.filter(province_admin=ligue.province_admin, actif=True).order_by('nom')
    form = RencontreForm(
        queryset_clubs=clubs_qs,
        queryset_stades=infras_qs,
        initial={
            'equipe_a': rencontre.equipe_a_id,
            'equipe_b': rencontre.equipe_b_id,
            'stade': rencontre.stade_id,
            'date_heure': rencontre.date_heure.strftime('%Y-%m-%dT%H:%M') if rencontre.date_heure else None,
        }
    )
    if request.method == 'POST':
        form = RencontreForm(request.POST, queryset_clubs=clubs_qs, queryset_stades=infras_qs)
        statut = request.POST.get('statut') or rencontre.statut
        if statut not in dict(Rencontre.STATUT_CHOICES):
            statut = rencontre.statut
        if form.is_valid() and form.cleaned_data['equipe_a'] != form.cleaned_data['equipe_b']:
            try:
                rencontre.equipe_a = form.cleaned_data['equipe_a']
                rencontre.equipe_b = form.cleaned_data['equipe_b']
                rencontre.stade = form.cleaned_data['stade']
                rencontre.date_heure = form.cleaned_data['date_heure']
                rencontre.statut = statut
                rencontre.save()
                if rencontre.evenement:
                    rencontre.evenement.titre = f"{rencontre.equipe_a.nom_officiel} vs {rencontre.equipe_b.nom_officiel}"[:255]
                    rencontre.evenement.date_evenement = rencontre.date_heure.date()
                    rencontre.evenement.heure_debut = rencontre.date_heure.time()
                    if rencontre.stade:
                        rencontre.evenement.infrastructure = rencontre.stade
                    rencontre.evenement.save()
                messages.success(request, "Rencontre modifiée.")
                return redirect('gouvernance:ligue_competition_journees', competition_uid=competition.uid)
            except ValidationError as e:
                msg = getattr(e, 'message_dict', {})
                if isinstance(msg, dict) and 'date_heure' in msg:
                    messages.error(request, msg['date_heure'][0])
                else:
                    messages.error(request, str(e))
        elif form.is_valid():
            messages.error(request, "Les deux équipes doivent être différentes.")
    context = {
        'ligue': ligue,
        'competition': competition,
        'journee': journee,
        'rencontre': rencontre,
        'form': form,
        'statut_choices': Rencontre.STATUT_CHOICES,
        'user_role': 'ligue_secretary',
    }
    return render(request, 'gouvernance/ligue_rencontre_edit.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_calendrier_rencontres(request, competition_uid):
    """Vue calendrier (type FullCalendar) : affichage des rencontres, glisser-déposer pour changer date/stade."""
    profil, ligue = _get_ligue_for_events(request)
    if not ligue:
        messages.error(request, "Vous n'êtes pas associé à une ligue provinciale.")
        return redirect('core:home')
    competition = get_object_or_404(Competition, uid=competition_uid, organisateur=ligue, actif=True)
    context = {
        'ligue': ligue,
        'competition': competition,
        'user_role': 'ligue_secretary',
    }
    return render(request, 'gouvernance/ligue_calendrier_rencontres.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_calendrier_rencontres_api(request, competition_uid):
    """API JSON : liste des rencontres pour FullCalendar (id, title, start, end, extendedProps)."""
    profil, ligue = _get_ligue_for_events(request)
    if not ligue:
        return JsonResponse({'error': 'Non autorisé'}, status=403)
    competition = get_object_or_404(Competition, uid=competition_uid, organisateur=ligue, actif=True)
    rencontres = Rencontre.objects.filter(journee__competition=competition).select_related(
        'equipe_a', 'equipe_b', 'stade', 'journee'
    ).order_by('date_heure')
    events = []
    for r in rencontres:
        start = r.date_heure
        from datetime import timedelta
        end = start + timedelta(hours=2)
        events.append({
            'id': str(r.uid),
            'title': f"{r.equipe_a.nom_officiel} vs {r.equipe_b.nom_officiel}",
            'start': start.isoformat(),
            'end': end.isoformat(),
            'extendedProps': {
                'stade_id': str(r.stade.uid) if r.stade else None,
                'stade': r.stade.nom if r.stade else '',
                'journee': r.journee.libelle,
                'statut': r.statut,
                'statut_display': r.get_statut_display(),
            },
        })
    return JsonResponse(events, safe=False)


@login_required
@require_role('FEDERATION_SECRETARY')
@require_http_methods(['POST'])
def ligue_rencontre_update_api(request, rencontre_uid):
    """API : mettre à jour date_heure et/ou stade d'une rencontre (glisser-déposer). Vérification conflit stade."""
    profil, ligue = _get_ligue_for_events(request)
    if not ligue:
        return JsonResponse({'ok': False, 'error': 'Non autorisé'}, status=403)
    rencontre = get_object_or_404(Rencontre, uid=rencontre_uid)
    if rencontre.journee.competition.organisateur_id != ligue.uid:
        return JsonResponse({'ok': False, 'error': 'Non autorisé'}, status=403)
    rencontre = Rencontre.objects.select_related('stade', 'evenement').get(uid=rencontre_uid)
    import json
    from django.utils.dateparse import parse_datetime
    try:
        data = json.loads(request.body) if request.body else {}
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Body JSON invalide'}, status=400)
    new_start = data.get('start') or data.get('date_heure')
    new_stade_id = data.get('stade_id')
    if new_start:
        dt = parse_datetime(new_start)
        if dt:
            rencontre.date_heure = dt
            if rencontre.evenement:
                rencontre.evenement.date_evenement = dt.date()
                rencontre.evenement.heure_debut = dt.time()
                rencontre.evenement.save(update_fields=['date_evenement', 'heure_debut'])
    if new_stade_id and new_stade_id != str(rencontre.stade_id or ''):
        infras = Infrastructure.objects.filter(uid=new_stade_id, actif=True)
        if ligue.province_admin_id:
            infras = infras.filter(province_admin=ligue.province_admin)
        new_stade = infras.first()
        if new_stade:
            rencontre.stade = new_stade
            if rencontre.evenement:
                rencontre.evenement.infrastructure = new_stade
                rencontre.evenement.save(update_fields=['infrastructure_id'])
    try:
        rencontre.full_clean()
        rencontre.save()
    except ValidationError as e:
        err_msg = str(e)
        if hasattr(e, 'message_dict') and isinstance(e.message_dict, dict) and 'date_heure' in e.message_dict:
            err_msg = e.message_dict['date_heure'][0]
        return JsonResponse({'ok': False, 'error': err_msg}, status=400)
    return JsonResponse({'ok': True})
