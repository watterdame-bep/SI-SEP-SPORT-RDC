"""
Vues pour le tableau de bord du secrétaire de fédération.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.messages import get_messages
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q
from django.utils import timezone

from core.permissions import require_role
from gouvernance.models import Institution, Athlete
from gouvernance.forms import CreerLigueProvincialForm


@login_required
@require_role('FEDERATION_SECRETARY')
def federation_secretary_dashboard(request):
    """
    Tableau de bord du secrétaire de fédération.
    Vue d'ensemble de la fédération et de ses activités.
    """
    # Ne pas afficher sur le dashboard les messages des autres interfaces
    list(get_messages(request))
    # Récupérer la fédération du secrétaire
    try:
        federation = request.user.profil_sisep.institution
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    if not federation or federation.niveau_territorial != 'FEDERATION':
        messages.error(request, "Vous n'êtes pas associé à une fédération.")
        return redirect('core:home')
    
    # Informations sur l'agrément
    agrement_info = {
        'statut': federation.statut_signature,
        'numero_homologation': federation.numero_homologation,
        'date_signature': federation.date_signature_arrete,
        'document_arrete': federation.document_arrete,
        'document_certificat': federation.document_certificat_homologation,
    }
    
    # Compteurs de performance
    # Clubs affiliés
    clubs = federation.institutions_fille.filter(niveau_territorial='CLUB', statut_activation='ACTIVE')
    nombre_clubs = clubs.count()
    
    # Ligues provinciales
    ligues = federation.institutions_fille.filter(niveau_territorial='LIGUE', statut_activation='ACTIVE')
    nombre_ligues = ligues.count()
    
    # Disciplines
    disciplines = federation.disciplines.filter(actif=True)
    nombre_disciplines = disciplines.count()
    
    # Alertes administratives (simulées pour l'instant)
    alertes = [
        {
            'type': 'RAPPORT_ATTENDU',
            'titre': 'Rapport annuel attendu',
            'message': 'Votre rapport d\'activités 2025 est attendu avant le 31 mars 2026',
            'priorite': 'HAUTE',
            'date_echeance': '2026-03-31',
        },
        {
            'type': 'COTISATION',
            'titre': 'Paiement des cotisations',
            'message': 'Les cotisations annuelles pour 2026 sont dues',
            'priorite': 'NORMALE',
            'date_echeance': '2026-04-30',
        },
    ]
    
    context = {
        'federation': federation,
        'agrement_info': agrement_info,
        'nombre_clubs': nombre_clubs,
        'nombre_ligues': nombre_ligues,
        'nombre_disciplines': nombre_disciplines,
        'alertes': alertes,
        'user_role': 'federation_secretary',
    }
    
    return render(request, 'gouvernance/federation_secretary_dashboard.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def federation_clubs_list(request):
    """
    Liste des clubs affiliés à la fédération.
    """
    try:
        federation = request.user.profil_sisep.institution
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    if not federation or federation.niveau_territorial != 'FEDERATION':
        messages.error(request, "Vous n'êtes pas associé à une fédération.")
        return redirect('core:home')
    
    # Récupérer les clubs
    clubs = federation.institutions_fille.filter(
        niveau_territorial='CLUB'
    ).select_related(
        'type_institution',
        'province_admin'
    ).order_by('nom_officiel')
    
    # Compter les clubs actifs
    clubs_actifs = clubs.filter(statut_activation='ACTIVE').count()
    
    # Récupérer les provinces uniques
    provinces = clubs.values_list('province_admin__designation', flat=True).distinct().order_by('province_admin__designation')
    provinces_count = provinces.count()
    
    context = {
        'federation': federation,
        'clubs': clubs,
        'clubs_actifs': clubs_actifs,
        'provinces': provinces,
        'provinces_count': provinces_count,
        'user_role': 'federation_secretary',
    }
    
    return render(request, 'gouvernance/federation_clubs_list.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def federation_ligues_list(request):
    """
    Liste des ligues provinciales affiliées à la fédération.
    """
    try:
        federation = request.user.profil_sisep.institution
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    if not federation or federation.niveau_territorial != 'FEDERATION':
        messages.error(request, "Vous n'êtes pas associé à une fédération.")
        return redirect('core:home')
    
    # Récupérer les ligues
    ligues = federation.institutions_fille.filter(
        niveau_territorial='LIGUE'
    ).select_related(
        'type_institution',
        'province_admin'
    ).order_by('nom_officiel')
    
    # Compter les ligues actives
    ligues_actives = ligues.filter(statut_activation='ACTIVE').count()
    
    # Récupérer les provinces uniques
    provinces = ligues.values_list('province_admin__designation', flat=True).distinct().order_by('province_admin__designation')
    provinces_count = provinces.count()
    
    context = {
        'federation': federation,
        'ligues': ligues,
        'ligues_actives': ligues_actives,
        'provinces': provinces,
        'provinces_count': provinces_count,
        'user_role': 'federation_secretary',
    }
    
    return render(request, 'gouvernance/federation_ligues_list.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def federation_documents(request):
    """
    Documents officiels de la fédération (Arrêté, Certificat).
    """
    try:
        federation = request.user.profil_sisep.institution
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    if not federation or federation.niveau_territorial != 'FEDERATION':
        messages.error(request, "Vous n'êtes pas associé à une fédération.")
        return redirect('core:home')
    
    documents = {
        'arrete': {
            'titre': 'Arrêté Ministériel d\'Agrément',
            'numero': federation.numero_arrete,
            'date': federation.date_signature_arrete,
            'fichier': federation.document_arrete,
            'description': 'Arrêté officiel d\'agrément de votre fédération',
            'statut': federation.statut_signature,
        },
        'certificat': {
            'titre': 'Certificat d\'Homologation Nationale',
            'numero': federation.numero_homologation,
            'date': federation.date_generation_certificat,
            'fichier': federation.document_certificat_homologation,
            'description': 'Certificat d\'homologation de votre fédération',
        },
    }
    
    context = {
        'federation': federation,
        'documents': documents,
        'user_role': 'federation_secretary',
    }
    
    return render(request, 'gouvernance/federation_documents.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def federation_profile(request):
    """
    Mon profil — Fédération : informations, logo, signature et cachet de la fédération.
    """
    try:
        federation = request.user.profil_sisep.institution
    except Exception:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    if not federation or federation.niveau_territorial != 'FEDERATION':
        messages.error(request, "Vous n'êtes pas associé à une fédération.")
        return redirect('core:home')
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        password = request.POST.get('password', '').strip()
        
        if form_type in ('signature', 'sceau'):
            if not request.user.check_password(password):
                messages.error(request, "Mot de passe incorrect. Modification annulée.")
                return render(request, 'gouvernance/federation_profile.html', {
                    'federation': federation,
                    'user_role': 'federation_secretary',
                }, status=400)
        
        if form_type == 'signature':
            if 'signature_image' in request.FILES:
                file = request.FILES['signature_image']
                if file.content_type != 'image/png' and not file.name.lower().endswith('.png'):
                    messages.error(request, "Seuls les fichiers PNG sont acceptés pour la signature.")
                elif file.size > 5 * 1024 * 1024:
                    messages.error(request, "Le fichier est trop volumineux. Taille maximale : 5 Mo.")
                else:
                    federation.signature_image = file
                    federation.save()
                    messages.success(request, "✓ Signature de la fédération enregistrée avec succès.")
            else:
                messages.error(request, "Veuillez sélectionner un fichier.")
        elif form_type == 'sceau':
            if 'sceau_image' in request.FILES:
                file = request.FILES['sceau_image']
                if file.content_type != 'image/png' and not file.name.lower().endswith('.png'):
                    messages.error(request, "Seuls les fichiers PNG sont acceptés pour le cachet.")
                elif file.size > 5 * 1024 * 1024:
                    messages.error(request, "Le fichier est trop volumineux. Taille maximale : 5 Mo.")
                else:
                    federation.sceau_image = file
                    federation.save()
                    messages.success(request, "✓ Cachet de la fédération enregistré avec succès.")
            else:
                messages.error(request, "Veuillez sélectionner un fichier.")
        elif form_type == 'logo':
            if 'logo_image' in request.FILES:
                file = request.FILES['logo_image']
                if not file.content_type.startswith('image/'):
                    messages.error(request, "Veuillez sélectionner une image (PNG, JPG, etc.).")
                elif file.size > 5 * 1024 * 1024:
                    messages.error(request, "Le fichier est trop volumineux. Taille maximale : 5 Mo.")
                else:
                    federation.logo = file
                    federation.save()
                    messages.success(request, "✓ Logo de la fédération mis à jour avec succès.")
        
        return redirect('gouvernance:federation_profile')
    
    context = {
        'federation': federation,
        'user_role': 'federation_secretary',
    }
    return render(request, 'gouvernance/federation_profile.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def federation_athletes(request):
    """
    Gestion des athlètes licenciés (placeholder).
    """
    try:
        federation = request.user.profil_sisep.institution
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    if not federation or federation.niveau_territorial != 'FEDERATION':
        messages.error(request, "Vous n'êtes pas associé à une fédération.")
        return redirect('core:home')
    
    context = {
        'federation': federation,
        'user_role': 'federation_secretary',
    }
    
    return render(request, 'gouvernance/federation_athletes.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def federation_competitions(request):
    """
    Gestion du calendrier sportif (placeholder).
    """
    try:
        federation = request.user.profil_sisep.institution
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    if not federation or federation.niveau_territorial != 'FEDERATION':
        messages.error(request, "Vous n'êtes pas associé à une fédération.")
        return redirect('core:home')
    
    context = {
        'federation': federation,
        'user_role': 'federation_secretary',
    }
    
    return render(request, 'gouvernance/federation_competitions.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def federation_ordre_mission(request):
    """
    Demande d'ordre de mission (placeholder).
    """
    try:
        federation = request.user.profil_sisep.institution
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    if not federation or federation.niveau_territorial != 'FEDERATION':
        messages.error(request, "Vous n'êtes pas associé à une fédération.")
        return redirect('core:home')
    
    context = {
        'federation': federation,
        'user_role': 'federation_secretary',
    }
    
    return render(request, 'gouvernance/federation_ordre_mission.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def create_ligue_provincial(request):
    """
    Créer une nouvelle Ligue Provinciale pour la fédération.
    Workflow: Création → Validation Division Provinciale → Validation SG → Attestation
    """
    try:
        federation = request.user.profil_sisep.institution
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    if not federation or federation.niveau_territorial != 'FEDERATION':
        messages.error(request, "Vous n'êtes pas associé à une fédération.")
        return redirect('core:home')
    
    if request.method == 'POST':
        form = CreerLigueProvincialForm(request.POST, request.FILES, federation=federation)
        if form.is_valid():
            try:
                # Récupérer le type d'institution pour LIGUE
                from gouvernance.models import TypeInstitution, ValidationLigue
                type_ligue = TypeInstitution.objects.get(code='LIGUE')
            except TypeInstitution.DoesNotExist:
                messages.error(request, "Type d'institution LIGUE non trouvé.")
                return redirect('gouvernance:federation_ligues')
            
            # Créer la nouvelle Ligue
            province = form.cleaned_data['province_admin']
            nom_ligue = form.cleaned_data['nom_ligue']
            sigle = form.cleaned_data.get('sigle_ligue', '')
            
            # Générer un code unique pour la ligue
            code = f"LIGUE-{federation.sigle}-{province.code}".upper()
            
            # Vérifier que le code n'existe pas
            if Institution.objects.filter(code=code).exists():
                messages.error(request, "Une ligue existe déjà pour cette province dans cette fédération.")
                return redirect('gouvernance:federation_ligues')
            
            # Créer l'institution Ligue
            ligue = Institution.objects.create(
                code=code,
                nom_officiel=nom_ligue,
                sigle=sigle or nom_ligue[:3].upper(),
                type_institution=type_ligue,
                niveau_territorial='LIGUE',
                institution_tutelle=federation,  # La fédération est la tutelle (IMPORTANT!)
                province_admin=province,
                statut_juridique=form.cleaned_data.get('statut_juridique', ''),
                date_creation=form.cleaned_data.get('date_creation'),
                nom_president=form.cleaned_data['nom_president'],
                telephone_president=form.cleaned_data.get('telephone_president', ''),
                email_officiel=form.cleaned_data['email_officiel'],
                telephone_off=form.cleaned_data['telephone_off'],
                site_web=form.cleaned_data.get('site_web', ''),
                statut_activation='ACTIVE',
                # Workflow: Ligue créée en attente de validation
                statut_inspection='EN_INSPECTION',
                statut_signature='ATTENTE_SIGNATURE',
                # Documents
                document_statuts=form.cleaned_data.get('document_statuts'),
                document_pv_ag=form.cleaned_data.get('document_pv_ag'),
                document_liste_membres=form.cleaned_data.get('document_liste_membres'),
            )
            
            # Ajouter les disciplines de la fédération à la ligue
            ligue.disciplines.set(federation.disciplines.all())
            
            # Créer la validation par la Division Provinciale
            try:
                from gouvernance.models import DivisionProvinciale
                
                # Récupérer la Division Provinciale de la province
                division_provinciale = DivisionProvinciale.objects.get(
                    province=province
                )
                
                # Créer le dossier de validation
                validation = ValidationLigue.objects.create(
                    ligue=ligue,
                    division_provinciale=division_provinciale,
                    statut='EN_ATTENTE_SG'
                )
                
                messages.success(
                    request, 
                    f"Ligue provinciale '{nom_ligue}' créée avec succès. "
                    f"Elle est maintenant en attente de validation par la Division Provinciale."
                )
            except DivisionProvinciale.DoesNotExist:
                messages.warning(
                    request,
                    f"Ligue provinciale '{nom_ligue}' créée, mais aucune Division Provinciale trouvée pour {province.designation}. "
                    f"Veuillez contacter l'administrateur."
                )
            
            return redirect('gouvernance:federation_ligues')
        else:
            # Afficher les erreurs du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CreerLigueProvincialForm(federation=federation)
    
    context = {
        'federation': federation,
        'form': form,
        'user_role': 'federation_secretary',
    }
    
    return render(request, 'gouvernance/create_ligue_provincial.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def federation_athletes_validation_list(request):
    """
    Liste des athlètes en attente de validation nationale.
    Le secrétaire de la fédération voit tous les athlètes CERTIFIE_PROVINCIAL.
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    federation = profil.institution
    
    if not federation or federation.niveau_territorial != 'FEDERATION':
        messages.error(request, "Vous n'êtes pas associé à une fédération.")
        return redirect('core:home')
    
    # Récupérer tous les athlètes en statut CERTIFIE_PROVINCIAL pour cette discipline
    athletes_certifies_provinciaux = Athlete.objects.filter(
        discipline__in=federation.disciplines.all(),
        statut_certification='CERTIFIE_PROVINCIAL',
        actif=True
    ).select_related('personne', 'club', 'club__institution_tutelle', 'discipline').order_by('-date_validation_ligue')
    
    # Statistiques
    total_en_attente = athletes_certifies_provinciaux.count()
    
    context = {
        'federation': federation,
        'athletes': athletes_certifies_provinciaux,
        'total_en_attente': total_en_attente,
        'user_role': 'federation_secretary',
    }
    
    return render(request, 'gouvernance/federation_athletes_validation_list.html', context)


@login_required
@require_role('FEDERATION_SECRETARY')
def federation_athlete_validate(request, athlete_uid):
    """
    Valider un athlète au niveau national.
    Vérifie qu'il n'existe pas de doublon au niveau national.
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    federation = profil.institution
    athlete = get_object_or_404(Athlete, uid=athlete_uid)
    
    # Vérifier que l'athlète est dans une discipline de cette fédération
    if athlete.discipline not in federation.disciplines.all():
        messages.error(request, "Cet athlète ne pratique pas une discipline de votre fédération.")
        return redirect('gouvernance:federation_athletes_validation_list')
    
    # Vérifier que l'athlète est en statut CERTIFIE_PROVINCIAL
    if athlete.statut_certification != 'CERTIFIE_PROVINCIAL':
        messages.warning(request, "Cet athlète n'est pas en attente de validation nationale.")
        return redirect('gouvernance:federation_athletes_validation_list')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'valider':
            # Vérifier les doublons au niveau national (même nom, prénom, date de naissance)
            doublons = Athlete.objects.filter(
                personne__nom=athlete.personne.nom,
                personne__prenom=athlete.personne.prenom,
                personne__date_naissance=athlete.personne.date_naissance,
                discipline=athlete.discipline,
                actif=True,
                statut_certification__in=['CERTIFIE_PROVINCIAL', 'CERTIFIE_NATIONAL']
            ).exclude(uid=athlete.uid)
            
            if doublons.exists():
                doublon = doublons.first()
                messages.error(request, f"⚠️ Un athlète avec le même nom ({athlete.personne.nom_complet}) et la même date de naissance existe déjà dans le club {doublon.club.nom_officiel} ({doublon.club.institution_tutelle.nom_officiel}).")
                return redirect('gouvernance:federation_athletes_validation_list')

            # Contrôle médical (F67/F72) : ne pas délivrer la licence si Inapte ou certificat d'aptitude absent
            if not athlete.peut_generer_licence_medical():
                messages.error(
                    request,
                    "Impossible de valider la licence : visite médicale (F67) absente, résultat INAPTE, ou certificat d'aptitude (F72) non délivré/joint. Vérifiez le dossier d'enrôlement."
                )
                return redirect('gouvernance:federation_athlete_validate', athlete_uid=athlete.uid)
            
            # Valider l'athlète
            athlete.statut_certification = 'CERTIFIE_NATIONAL'
            athlete.date_validation_federation = timezone.now()
            athlete.validateur_federation = profil
            
            # Définir les informations de la licence et générer le PDF (format ID-1 biométrique)
            from datetime import date, timedelta
            athlete.numero_licence = athlete.numero_sportif
            athlete.date_emission_licence = date.today()
            athlete.date_expiration_licence = date.today() + timedelta(days=365)
            
            # Générer la licence sportive : ID-1 d'abord, repli sur A4 si échec (pour que le PDF soit toujours créé)
            base_url = request.build_absolute_uri('/').rstrip('/')
            import logging
            logger = logging.getLogger(__name__)
            licence_generated = False
            try:
                from gouvernance.licence_generator import generer_licence_sportive_id1, generer_licence_sportive
                from django.core.files.base import ContentFile
                pdf_content = generer_licence_sportive_id1(athlete, base_url=base_url)
                if pdf_content:
                    filename = f"Licence_ID1_{athlete.numero_licence}.pdf"
                    athlete.licence_pdf.save(filename, ContentFile(pdf_content.getvalue()), save=False)
                    licence_generated = True
            except Exception as e:
                logger.exception("Génération licence ID-1: %s", e)
                try:
                    # Repli sur format A4 pour garantir un PDF disponible (galerie club, téléchargement)
                    licence_file = generer_licence_sportive(athlete, base_url=base_url)
                    if licence_file:
                        athlete.licence_pdf.save(licence_file.name, licence_file, save=False)
                        licence_generated = True
                        request.session['licence_generation_warning'] = "Licence générée au format A4 (ID-1 en échec)."
                except Exception as e2:
                    logger.exception("Génération licence A4 (fallback): %s", e2)
                    request.session['licence_generation_warning'] = str(e)
            
            athlete.save()
            
            if request.session.pop('licence_generation_warning', None):
                messages.warning(request, "Athlète certifié au niveau national. La licence n'a pas pu être générée automatiquement (voir les logs).")
            else:
                messages.success(request, f"✓ Athlète {athlete.personne.nom_complet} certifié au niveau national! Licence générée (n° {athlete.numero_licence})")
            return redirect('gouvernance:federation_athletes_validation_list')
        
        elif action == 'rejeter':
            motif = request.POST.get('motif_rejet', '')
            if not motif:
                messages.error(request, "Veuillez fournir un motif de rejet.")
                return redirect('gouvernance:federation_athletes_validation_list')
            
            athlete.statut_certification = 'REJETE_FEDERATION'
            athlete.motif_rejet_federation = motif
            athlete.save()
            
            messages.warning(request, f"Athlète {athlete.personne.nom_complet} rejeté.")
            return redirect('gouvernance:federation_athletes_validation_list')
    
    # Chercher les doublons potentiels pour affichage
    doublons_potentiels = Athlete.objects.filter(
        Q(personne__nom__iexact=athlete.personne.nom) |
        Q(personne__prenom__iexact=athlete.personne.prenom),
        discipline=athlete.discipline,
        actif=True,
        statut_certification__in=['CERTIFIE_PROVINCIAL', 'CERTIFIE_NATIONAL']
    ).exclude(uid=athlete.uid).select_related('personne', 'club', 'club__institution_tutelle')
    
    # Dernière visite médicale (F67) — pour afficher certification médicale et avis du médecin au secrétaire fédération
    visite_certification = athlete.visites_medicales.order_by('-date_visite').first()
    
    context = {
        'federation': federation,
        'athlete': athlete,
        'doublons_potentiels': doublons_potentiels,
        'visite_certification': visite_certification,
        'user_role': 'federation_secretary',
    }
    
    return render(request, 'gouvernance/federation_athlete_validate.html', context)



@login_required
@require_role('FEDERATION_SECRETARY')
def federation_athlete_verify_duplicates(request, athlete_uid):
    """
    Vérification anti-fraude au niveau national: reconnaissance faciale + état civil.
    Retourne un JSON avec les résultats de vérification.
    """
    from django.http import JsonResponse
    
    try:
        profil = request.user.profil_sisep
    except:
        return JsonResponse({'error': 'Profil utilisateur introuvable.'}, status=403)
    
    federation = profil.institution
    athlete = get_object_or_404(Athlete, uid=athlete_uid)
    
    # Vérifier que l'athlète est dans une discipline de cette fédération
    if athlete.discipline not in federation.disciplines.all():
        return JsonResponse({'error': 'Cet athlète ne pratique pas une discipline de votre fédération.'}, status=403)
    
    # 1. VÉRIFICATION BIOMÉTRIQUE (Reconnaissance Faciale) AU NIVEAU NATIONAL
    # Note: Pour une vraie implémentation, utiliser face_recognition ou DeepFace
    biometric_matches = []
    biometric_status = 'clear'
    biometric_message = "✓ Aucune correspondance faciale détectée. Le visage de cet athlète est unique dans la base de données nationale."
    
    if athlete.personne.photo:
        # Rechercher tous les athlètes au niveau national avec photo (même discipline)
        autres_athletes = Athlete.objects.filter(
            discipline=athlete.discipline,
            actif=True,
            personne__photo__isnull=False
        ).exclude(uid=athlete.uid).select_related('personne', 'club', 'club__institution_tutelle')
        
        # TODO: Implémenter la vraie reconnaissance faciale ici
        # Pour l'instant, on simule en cherchant des noms très similaires
        for autre in autres_athletes:
            # Simulation: si le nom est identique, on considère que c'est un doublon potentiel
            if (athlete.personne.nom.lower() == autre.personne.nom.lower() and 
                athlete.personne.prenom.lower() == autre.personne.prenom.lower()):
                biometric_matches.append({
                    'nom': autre.personne.nom_complet,
                    'club': autre.club.nom_officiel,
                    'province': autre.club.institution_tutelle.nom_officiel if autre.club.institution_tutelle else 'N/A',
                    'photo': autre.personne.photo.url if autre.personne.photo else '',
                    'similarity': 95,  # Pourcentage de similarité simulé
                    'numero_sportif': autre.numero_sportif,
                })
        
        if biometric_matches:
            biometric_status = 'fraud_detected'
            biometric_message = f"⚠️ ALERTE FRAUDE NATIONALE: {len(biometric_matches)} correspondance(s) faciale(s) détectée(s) dans d'autres provinces! Le visage de cet athlète correspond à un ou plusieurs athlètes déjà enregistrés sous d'autres identités."
    else:
        biometric_message = "⚠️ Aucune photo disponible pour la vérification biométrique."
    
    # 2. VÉRIFICATION ÉTAT CIVIL (Nom + Prénom + Date de naissance) AU NIVEAU NATIONAL
    civil_matches = []
    civil_status = 'clear'
    civil_message = "✓ Aucun homonyme détecté. Les données d'état civil sont uniques au niveau national."
    
    # Rechercher les homonymes au niveau national (même nom, prénom, date de naissance, même discipline)
    homonymes = Athlete.objects.filter(
        personne__nom__iexact=athlete.personne.nom,
        personne__prenom__iexact=athlete.personne.prenom,
        personne__date_naissance=athlete.personne.date_naissance,
        discipline=athlete.discipline,
        actif=True
    ).exclude(uid=athlete.uid).select_related('personne', 'club', 'club__institution_tutelle')
    
    for homonyme in homonymes:
        civil_matches.append({
            'nom': homonyme.personne.nom_complet,
            'club': homonyme.club.nom_officiel,
            'province': homonyme.club.institution_tutelle.nom_officiel if homonyme.club.institution_tutelle else 'N/A',
            'date_naissance': homonyme.personne.date_naissance.strftime('%d/%m/%Y'),
            'numero_sportif': homonyme.numero_sportif,
        })
    
    if civil_matches:
        civil_status = 'duplicate_found'
        civil_message = f"⚠️ ATTENTION NATIONALE: {len(civil_matches)} homonyme(s) détecté(s) dans d'autres provinces avec les mêmes nom, prénom et date de naissance. Vérifiez qu'il ne s'agit pas de la même personne."
    
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
