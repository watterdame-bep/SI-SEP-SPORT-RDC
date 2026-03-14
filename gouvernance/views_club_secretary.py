"""
Vues pour le Secrétaire du Club.
Gestion des athlètes, staff, infrastructures et compétitions du club.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.messages import get_messages
from django.db.models import Count, Q

from core.permissions import require_role
from gouvernance.models import Institution


@login_required
@require_role('CLUB_SECRETARY')
def club_secretary_dashboard(request):
    """
    Tableau de bord du Secrétaire du Club.
    Vue d'ensemble du club avec statistiques et accès rapide.
    """
    # Ne pas afficher sur le dashboard les messages des autres interfaces
    list(get_messages(request))
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    club = profil.institution
    
    if not club or club.niveau_territorial != 'CLUB':
        messages.error(request, "Vous n'êtes pas associé à un club.")
        return redirect('core:home')
    
    # Récupérer la ligue parente
    ligue = club.institution_tutelle
    
    # Statistiques (à implémenter avec les modèles réels)
    stats = {
        'athletes_total': 0,  # TODO: Implémenter avec le modèle Licence
        'athletes_hommes': 0,
        'athletes_femmes': 0,
        'staff_total': 0,  # TODO: Implémenter avec le modèle Staff
        'entraîneurs': 0,
        'medecins': 0,
        'competitions_a_venir': 0,  # TODO: Implémenter avec le modèle Compétition
    }
    
    context = {
        'club': club,
        'ligue': ligue,
        'stats': stats,
        'user_role': 'club_secretary',
    }
    
    return render(request, 'gouvernance/club_secretary_dashboard.html', context)


@login_required
@require_role('CLUB_SECRETARY')
def club_identity(request):
    """
    Identité du club : informations générales, logo, couleurs.
    """
    try:
        profil = request.user.profil_sisep
    except Exception:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    club = profil.institution
    
    if not club or club.niveau_territorial != 'CLUB':
        messages.error(request, "Vous n'êtes pas associé à un club.")
        return redirect('core:home')
    
    if request.method == 'POST' and 'logo_image' in request.FILES:
        file = request.FILES['logo_image']
        if not file.content_type.startswith('image/'):
            messages.error(request, "Veuillez sélectionner une image (PNG, JPG, etc.).")
        elif file.size > 5 * 1024 * 1024:
            messages.error(request, "Le fichier est trop volumineux. Taille maximale : 5 Mo.")
        else:
            club.logo = file
            club.save()
            messages.success(request, "✓ Logo du club mis à jour avec succès.")
        return redirect('gouvernance:club_identity')
    
    context = {
        'club': club,
        'user_role': 'club_secretary',
    }
    
    return render(request, 'gouvernance/club_identity.html', context)


@login_required
@require_role('CLUB_SECRETARY')
def club_documents(request):
    """
    Documents officiels du club : Acte d'Affiliation, Statuts, etc.
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    club = profil.institution
    
    if not club or club.niveau_territorial != 'CLUB':
        messages.error(request, "Vous n'êtes pas associé à un club.")
        return redirect('core:home')
    
    context = {
        'club': club,
        'user_role': 'club_secretary',
    }
    
    return render(request, 'gouvernance/club_documents.html', context)


@login_required
@require_role('CLUB_SECRETARY')
def club_athletes_list(request):
    """
    Liste de tous les athlètes du club (effectif global).
    """
    from gouvernance.models import Athlete
    from gouvernance.forms import AthleteForm
    
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    club = profil.institution
    
    if not club or club.niveau_territorial != 'CLUB':
        messages.error(request, "Vous n'êtes pas associé à un club.")
        return redirect('core:home')
    
    # Récupérer tous les athlètes du club
    athletes = Athlete.objects.filter(club=club, actif=True).select_related('personne', 'discipline').order_by('personne__nom', 'personne__prenom')
    
    # Statistiques
    total_athletes = athletes.count()
    athletes_actifs = athletes.filter(statut='ACTIF').count()
    athletes_masculins = athletes.filter(personne__sexe='M').count()
    athletes_feminins = athletes.filter(personne__sexe='F').count()
    
    context = {
        'club': club,
        'athletes': athletes,
        'total_athletes': total_athletes,
        'athletes_actifs': athletes_actifs,
        'athletes_masculins': athletes_masculins,
        'athletes_feminins': athletes_feminins,
        'user_role': 'club_secretary',
    }
    
    return render(request, 'gouvernance/club_athletes_list.html', context)


@login_required
@require_role('CLUB_SECRETARY')
def club_license_requests(request):
    """
    Suivi des demandes de licences : Provisoire, Enrôlé, Homologué.
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    club = profil.institution
    
    if not club or club.niveau_territorial != 'CLUB':
        messages.error(request, "Vous n'êtes pas associé à un club.")
        return redirect('core:home')
    
    # TODO: Récupérer les demandes de licences du club
    licenses = []
    
    context = {
        'club': club,
        'licenses': licenses,
        'user_role': 'club_secretary',
    }
    
    return render(request, 'gouvernance/club_license_requests.html', context)


@login_required
@require_role('CLUB_SECRETARY')
def club_athlete_registration(request):
    """
    Inscription d'un nouvel athlète (F08).
    """
    from gouvernance.models import Athlete
    from gouvernance.forms import AthleteForm
    
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    club = profil.institution
    
    if not club or club.niveau_territorial != 'CLUB':
        messages.error(request, "Vous n'êtes pas associé à un club.")
        return redirect('core:home')
    
    if request.method == 'POST':
        form = AthleteForm(request.POST, request.FILES, club=club)
        if form.is_valid():
            athlete = form.save(club)
            messages.success(request, f"✓ Athlète {athlete.nom_complet} enregistré avec succès!")
            return redirect('gouvernance:club_athletes_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = AthleteForm(club=club)
    
    context = {
        'club': club,
        'form': form,
        'user_role': 'club_secretary',
    }
    
    return render(request, 'gouvernance/club_athlete_registration.html', context)


@login_required
@require_role('CLUB_SECRETARY')
def club_staff(request):
    """
    Gestion du staff technique : Entraîneurs & Médecins.
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    club = profil.institution
    
    if not club or club.niveau_territorial != 'CLUB':
        messages.error(request, "Vous n'êtes pas associé à un club.")
        return redirect('core:home')
    
    # TODO: Récupérer les entraîneurs et médecins du club
    staff = []
    
    context = {
        'club': club,
        'staff': staff,
        'user_role': 'club_secretary',
    }
    
    return render(request, 'gouvernance/club_staff.html', context)


@login_required
@require_role('CLUB_SECRETARY')
def club_infrastructure(request):
    """
    Détails du stade/centre d'entraînement du club.
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    club = profil.institution
    
    if not club or club.niveau_territorial != 'CLUB':
        messages.error(request, "Vous n'êtes pas associé à un club.")
        return redirect('core:home')
    
    # TODO: Récupérer les infrastructures du club
    infrastructure = None
    
    context = {
        'club': club,
        'infrastructure': infrastructure,
        'user_role': 'club_secretary',
    }
    
    return render(request, 'gouvernance/club_infrastructure.html', context)


@login_required
@require_role('CLUB_SECRETARY')
def club_competitions_calendar(request):
    """
    Calendrier des compétitions : matchs à venir.
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    club = profil.institution
    
    if not club or club.niveau_territorial != 'CLUB':
        messages.error(request, "Vous n'êtes pas associé à un club.")
        return redirect('core:home')
    
    # TODO: Récupérer les compétitions du club
    competitions = []
    
    context = {
        'club': club,
        'competitions': competitions,
        'user_role': 'club_secretary',
    }
    
    return render(request, 'gouvernance/club_competitions_calendar.html', context)


@login_required
@require_role('CLUB_SECRETARY')
def club_match_sheets(request):
    """
    Feuilles de match : historique des rencontres.
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    club = profil.institution
    
    if not club or club.niveau_territorial != 'CLUB':
        messages.error(request, "Vous n'êtes pas associé à un club.")
        return redirect('core:home')
    
    # TODO: Récupérer les feuilles de match du club
    match_sheets = []
    
    context = {
        'club': club,
        'match_sheets': match_sheets,
        'user_role': 'club_secretary',
    }
    
    return render(request, 'gouvernance/club_match_sheets.html', context)


@login_required
@require_role('CLUB_SECRETARY')
def club_licences_galerie(request):
    """
    Ma Galerie de Licences — Licence numérique pour le club.
    Liste tous les athlètes du club certifiés (CERTIFIE_NATIONAL) avec une vignette
    simplifiée (Photo + Nom + QR Code) optimisée mobile, et bouton Télécharger le PDF.
    """
    import base64
    import io
    import qrcode
    from gouvernance.models import Athlete

    try:
        profil = request.user.profil_sisep
    except Exception:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')

    club = profil.institution
    if not club or club.niveau_territorial != 'CLUB':
        messages.error(request, "Vous n'êtes pas associé à un club.")
        return redirect('core:home')

    athletes = Athlete.objects.filter(
        club=club,
        statut_certification='CERTIFIE_NATIONAL',
        actif=True
    ).select_related('personne', 'discipline').order_by('personne__nom', 'personne__prenom')

    base_url = request.build_absolute_uri('/').rstrip('/')
    athletes_with_qr = []
    for athlete in athletes:
        verification_url = f"{base_url}/gouvernance/verifier-athlete/{athlete.uid}/"
        try:
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=4, border=1)
            qr.add_data(verification_url)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            buf = io.BytesIO()
            qr_img.save(buf, format='PNG')
            qr_b64 = base64.b64encode(buf.getvalue()).decode()
            qr_data_url = f"data:image/png;base64,{qr_b64}"
        except Exception:
            qr_data_url = None
        athletes_with_qr.append({'athlete': athlete, 'qr_data_url': qr_data_url})

    context = {
        'club': club,
        'athletes_with_qr': athletes_with_qr,
        'user_role': 'club_secretary',
    }
    return render(request, 'gouvernance/club_licences_galerie.html', context)


@login_required
@require_role('CLUB_SECRETARY')
def club_athlete_download_licence(request, athlete_uid):
    """
    Télécharger la licence PDF d'un athlète certifié nationalement.
    """
    from django.http import FileResponse, Http404
    from gouvernance.models import Athlete
    
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    club = profil.institution
    
    if not club or club.niveau_territorial != 'CLUB':
        messages.error(request, "Vous n'êtes pas associé à un club.")
        return redirect('core:home')
    
    # Récupérer l'athlète
    athlete = get_object_or_404(Athlete, uid=athlete_uid, club=club)
    
    # Vérifier que l'athlète est certifié nationalement
    if athlete.statut_certification != 'CERTIFIE_NATIONAL':
        messages.error(request, "Cet athlète n'est pas encore certifié nationalement.")
        return redirect('gouvernance:club_athletes_list')
    
    # Vérifier que la licence existe
    if not athlete.licence_pdf:
        messages.error(request, "La licence de cet athlète n'a pas encore été générée.")
        return redirect('gouvernance:club_athletes_list')
    
    # Retourner le fichier PDF
    try:
        return FileResponse(
            athlete.licence_pdf.open('rb'),
            content_type='application/pdf',
            as_attachment=True,
            filename=f"Licence_{athlete.numero_licence or athlete.numero_sportif}.pdf"
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors du téléchargement de la licence: {str(e)}")
        raise Http404("Fichier de licence introuvable.")


@login_required
def licence_f22_print(request, athlete_uid):
    """
    Page d'impression de la licence F22 au format ID-1 (85,6 mm × 54 mm).
    Pour imprimante à badges (Evolis, Zebra). Accessible au club (ses athlètes) et à la fédération.
    """
    from django.http import Http404
    from core.models import RoleUtilisateur
    from gouvernance.models import Athlete
    import base64
    import io
    import qrcode

    athlete = get_object_or_404(Athlete, uid=athlete_uid, actif=True)
    try:
        profil = request.user.profil_sisep
        if not profil.actif or profil.role not in (RoleUtilisateur.CLUB_SECRETARY, RoleUtilisateur.FEDERATION_SECRETARY):
            raise Http404("Accès non autorisé.")
    except Exception:
        raise Http404("Profil introuvable.")

    # Permission : club (ses athlètes), ligue (athlètes des clubs de la ligue), fédération (sa discipline)
    allowed = False
    federation_nom = None
    federation_logo_url = None
    if profil.institution and profil.institution.niveau_territorial == 'CLUB':
        if athlete.club_id == profil.institution.uid:
            allowed = True
            if athlete.club and athlete.club.institution_tutelle:
                federation_nom = athlete.club.institution_tutelle.nom_officiel
                if getattr(athlete.club.institution_tutelle, 'logo', None) and athlete.club.institution_tutelle.logo:
                    try:
                        federation_logo_url = athlete.club.institution_tutelle.logo.url
                    except Exception:
                        pass
    elif profil.institution and profil.institution.niveau_territorial == 'FEDERATION':
        if athlete.discipline and hasattr(profil.institution, 'disciplines') and athlete.discipline in profil.institution.disciplines.all():
            allowed = True
            federation_nom = profil.institution.nom_officiel
            if getattr(profil.institution, 'logo', None) and profil.institution.logo:
                try:
                    federation_logo_url = profil.institution.logo.url
                except Exception:
                    pass
    elif profil.institution and profil.institution.niveau_territorial in ('LIGUE', 'LIGUE_PROVINCIALE'):
        if athlete.club and athlete.club.institution_tutelle_id == profil.institution.uid:
            allowed = True
            federation_nom = profil.institution.nom_officiel
            if getattr(profil.institution, 'logo', None) and profil.institution.logo:
                try:
                    federation_logo_url = profil.institution.logo.url
                except Exception:
                    pass

    if not allowed:
        raise Http404("Vous n'êtes pas autorisé à imprimer cette licence.")

    if athlete.statut_certification != 'CERTIFIE_NATIONAL':
        raise Http404("Cet athlète n'est pas certifié nationalement.")

    # QR code en data URL pour vérification
    base_url = request.build_absolute_uri('/').rstrip('/')
    verification_url = f"{base_url}/gouvernance/verifier-athlete/{athlete.uid}/"
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=4, border=1)
    qr.add_data(verification_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    qr_img.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode()
    qr_data_url = f"data:image/png;base64,{qr_b64}"

    # Adresse et lieu de naissance pour la licence
    adresse_texte = ""
    if getattr(athlete.personne, 'adresse', None) and athlete.personne.adresse:
        adr = athlete.personne.adresse
        parts = [p for p in [getattr(adr, 'avenue', None), getattr(adr, 'numero', None) and str(adr.numero), getattr(adr, 'commune', None)] if p]
        adresse_texte = ", ".join(parts) if parts else ""
    lieu_naissance_texte = ""
    if getattr(athlete.personne, 'lieu_naissance', None) and athlete.personne.lieu_naissance:
        lieu_naissance_texte = athlete.personne.lieu_naissance.designation or ""

    context = {
        'athlete': athlete,
        'federation_nom': federation_nom or "Fédération",
        'federation_logo_url': federation_logo_url,
        'qr_data_url': qr_data_url,
        'adresse_texte': adresse_texte,
        'lieu_naissance_texte': lieu_naissance_texte,
    }
    return render(request, 'gouvernance/licence_f22_print.html', context)

