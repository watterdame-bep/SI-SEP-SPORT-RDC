# -*- coding: utf-8 -*-
"""
Vues pour le Médecin Inspecteur / Validateur de la Ligue Provinciale.
Accès limité à la gestion des dossiers médicaux des athlètes de sa ligue.
"""
import re
from datetime import datetime
from decimal import Decimal as Dec

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
from django.contrib import messages
from django.contrib.messages import get_messages
from django.utils import timezone

from django.http import JsonResponse
from core.permissions import require_role
from gouvernance.models import Institution, Athlete, VisiteMedicale, TypeExamen, ResultatExamenVisite
from gouvernance.models import CaptureEmpreintes


@login_required
@require_role('MEDECIN_INSPECTEUR')
def medecin_dashboard(request):
    """
    Tableau de bord du Médecin Inspecteur : vue d'ensemble des athlètes de sa ligue et de leurs dossiers médicaux.
    """
    # Ne pas afficher sur le dashboard les messages des autres interfaces (examen F67, etc.)
    list(get_messages(request))
    try:
        profil = request.user.profil_sisep
    except Exception:
        return redirect('core:home')
    ligue = profil.institution
    if not ligue or ligue.niveau_territorial not in ('LIGUE', 'LIGUE_PROVINCIALE'):
        return redirect('core:home')
    clubs = Institution.objects.filter(
        niveau_territorial='CLUB',
        institution_tutelle=ligue
    )
    athletes = Athlete.objects.filter(
        club__in=clubs,
        actif=True
    ).select_related('personne', 'club', 'discipline').order_by('personne__nom', 'personne__prenom')
    athletes_avec_visite = Athlete.objects.filter(
        club__in=clubs,
        actif=True,
        visites_medicales__isnull=False
    ).distinct()
    athletes_sans_visite = athletes.exclude(
        pk__in=athletes_avec_visite.values_list('pk', flat=True)
    )
    athletes_count = athletes.count()
    dernieres_visites = VisiteMedicale.objects.filter(
        athlete__club__in=clubs
    ).select_related('athlete', 'athlete__personne', 'athlete__club').order_by('-date_visite')[:15]
    context = {
        'ligue': ligue,
        'athletes_count': athletes_count,
        'athletes_avec_visite_count': athletes_avec_visite.count(),
        'athletes_sans_visite_count': athletes_sans_visite.count(),
        'dernieres_visites': dernieres_visites,
        'user_role': 'medecin_inspecteur',
    }
    return render(request, 'gouvernance/medecin_dashboard.html', context)


@login_required
@require_role('MEDECIN_INSPECTEUR')
def medecin_athletes_list(request):
    """Liste des athlètes de la ligue avec accès au dossier médical."""
    try:
        profil = request.user.profil_sisep
    except Exception:
        return redirect('core:home')
    ligue = profil.institution
    if not ligue or ligue.niveau_territorial not in ('LIGUE', 'LIGUE_PROVINCIALE'):
        return redirect('core:home')
    clubs = Institution.objects.filter(niveau_territorial='CLUB', institution_tutelle=ligue)
    athletes = Athlete.objects.filter(
        club__in=clubs,
        actif=True
    ).select_related('personne', 'club', 'discipline').annotate(
        nb_visites=Count('visites_medicales')
    ).order_by('personne__nom', 'personne__prenom')
    total_athletes = athletes.count()
    total_avec_visite = Athlete.objects.filter(club__in=clubs, actif=True).filter(visites_medicales__isnull=False).distinct().count()
    context = {
        'ligue': ligue,
        'athletes': athletes,
        'total_athletes': total_athletes,
        'total_avec_visite': total_avec_visite,
        'user_role': 'medecin_inspecteur',
    }
    return render(request, 'gouvernance/medecin_athletes_list.html', context)


@login_required
@require_role('MEDECIN_INSPECTEUR')
def medecin_athlete_dossier(request, athlete_uid):
    """
    Dossier médical d'un athlète : visites médicales (F67), certificats, résultats.
    Le médecin ne peut accéder qu'aux athlètes des clubs de sa ligue.
    """
    try:
        profil = request.user.profil_sisep
    except Exception:
        return redirect('core:home')
    ligue = profil.institution
    if not ligue or ligue.niveau_territorial not in ('LIGUE', 'LIGUE_PROVINCIALE'):
        return redirect('core:home')
    athlete = get_object_or_404(Athlete, uid=athlete_uid, actif=True)
    if athlete.club.institution_tutelle != ligue:
        return redirect('gouvernance:medecin_dashboard')
    visites = athlete.visites_medicales.prefetch_related('resultats_examens__type_examen').order_by('-date_visite')
    visites_list = list(visites)
    date_min = min(v.date_visite for v in visites_list) if visites_list else None
    date_max = max(v.date_visite for v in visites_list) if visites_list else None
    context = {
        'ligue': ligue,
        'athlete': athlete,
        'visites': visites_list,
        'date_min': date_min,
        'date_max': date_max,
        'user_role': 'medecin_inspecteur',
    }
    return render(request, 'gouvernance/medecin_athlete_dossier.html', context)


def _get_medecin_ligue_context(request):
    """Retourne (profil, ligue) ou (None, None) si accès invalide."""
    try:
        profil = request.user.profil_sisep
    except Exception:
        return None, None
    ligue = profil.institution
    if not ligue or ligue.niveau_territorial not in ('LIGUE', 'LIGUE_PROVINCIALE'):
        return None, None
    return profil, ligue


@login_required
@require_role('MEDECIN_INSPECTEUR')
def medecin_athletes_en_attente_examen(request):
    """Liste des athlètes transférés par le secrétaire, en attente de l'examen médical (F67)."""
    profil, ligue = _get_medecin_ligue_context(request)
    if not ligue:
        return redirect('core:home')
    clubs = Institution.objects.filter(
        niveau_territorial='CLUB',
        institution_tutelle=ligue
    )
    athletes = Athlete.objects.filter(
        club__in=clubs,
        actif=True,
        statut_certification='EN_ATTENTE_EXAMEN_MEDICAL'
    ).select_related('personne', 'club', 'discipline').order_by('date_enrolement', 'personne__nom', 'personne__prenom')
    total_en_attente = athletes.count()
    context = {
        'ligue': ligue,
        'athletes': athletes,
        'total_en_attente': total_en_attente,
        'user_role': 'medecin_inspecteur',
    }
    return render(request, 'gouvernance/medecin_athletes_en_attente_examen.html', context)


@login_required
@require_role('MEDECIN_INSPECTEUR')
def medecin_athlete_examen_medical(request, athlete_uid):
    """
    Formulaire Examen médical (F67) — visite d'homologation pour un athlète transféré par le secrétaire.
    GET : affiche le formulaire ; POST : enregistre la visite médicale et passe l'athlète en EN_ATTENTE_VALIDATION_LIGUE.
    """
    profil, ligue = _get_medecin_ligue_context(request)
    if not ligue:
        return redirect('core:home')
    athlete = get_object_or_404(Athlete, uid=athlete_uid, actif=True)
    if athlete.club.institution_tutelle != ligue:
        messages.error(request, "Cet athlète n'appartient pas à un club de votre ligue.")
        return redirect('gouvernance:medecin_athletes_en_attente_examen')
    if athlete.statut_certification != 'EN_ATTENTE_EXAMEN_MEDICAL':
        messages.warning(request, "Cet athlète n'est plus en attente d'examen médical.")
        return redirect('gouvernance:medecin_athletes_en_attente_examen')

    def _render_form_with_errors(request, athlete, ligue, form_data):
        """Réaffiche le formulaire F67 avec les données soumises pour ne pas perdre la saisie en cas d'erreur."""
        types_examen = TypeExamen.objects.filter(actif=True).order_by('ordre', 'libelle')
        has_examens_optionnels = any(not te.obligatoire for te in types_examen)
        medecin_nom = (form_data.get('medecin_nom') or '').strip() if form_data else ''
        if not medecin_nom and profil:
            try:
                if getattr(profil, 'agent', None) and profil.agent.personne_id:
                    medecin_nom = profil.agent.personne.nom_complet
                elif getattr(profil, 'personne', None) and profil.personne_id:
                    medecin_nom = profil.personne.nom_complet
            except Exception:
                pass
        if not medecin_nom and request.user:
            medecin_nom = request.user.get_full_name() or (getattr(request.user, 'email', '') or '')
        has_emp = False
        try:
            has_emp = athlete.capture_empreintes.has_templates
        except CaptureEmpreintes.DoesNotExist:
            pass
        from django.conf import settings
        context = {
            'ligue': ligue,
            'athlete': athlete,
            'types_examen': types_examen,
            'has_examens_optionnels': has_examens_optionnels,
            'medecin_nom': medecin_nom or '',
            'form_data': form_data or {},
            'user_role': 'medecin_inspecteur',
            'has_empreintes_template': has_emp,
            'morpho_service_uri': getattr(settings, 'MORPHO_SERVICE_URI', 'http://localhost:8032/morfinenroll/'),
        }
        return render(request, 'gouvernance/medecin_athlete_examen_medical.html', context)

    if request.method == 'POST':
        # Construire form_data pour réaffichage en cas d'erreur (une valeur par clé)
        form_data = {k: (v[0] if v else '') for k, v in request.POST.lists()}

        date_visite_str = request.POST.get('date_visite') or request.POST.get('date_test_medical')
        medecin_nom = (request.POST.get('medecin_nom') or '').strip()
        medecin_etablissement = ''
        resultat_global = request.POST.get('resultat_global')
        taille_raw = request.POST.get('taille')
        poids_raw = request.POST.get('poids')
        notes_examen = request.POST.get('notes_examen_clinique', '')
        recommandations_securite = (request.POST.get('recommandations_securite') or '').strip()
        groupe_sanguin_rh = (request.POST.get('groupe_sanguin_rh') or '').strip()
        certificat_aptitude_delivre = request.POST.get('certificat_aptitude_delivre') == '1'
        demande_surclassement = request.POST.get('demande_surclassement') == '1'
        test_greulich_ok = request.POST.get('test_greulich_pyle_ok') == '1'

        certificat_aptitude_joint = request.FILES.get('certificat_aptitude_joint')
        radiographie_poignet = request.FILES.get('radiographie_poignet_joint')

        if not taille_raw:
            messages.error(request, "Veuillez saisir la taille de l'athlète (en cm).")
            return _render_form_with_errors(request, athlete, ligue, form_data)
        try:
            taille_val = int(taille_raw)
            if taille_val < 50 or taille_val > 250:
                messages.error(request, "La taille doit être entre 50 et 250 cm.")
                return _render_form_with_errors(request, athlete, ligue, form_data)
        except (ValueError, TypeError):
            messages.error(request, "Taille invalide.")
            return _render_form_with_errors(request, athlete, ligue, form_data)
        if not poids_raw:
            messages.error(request, "Veuillez saisir le poids de l'athlète (en kg).")
            return _render_form_with_errors(request, athlete, ligue, form_data)
        try:
            poids_val = Dec(poids_raw.replace(',', '.'))
            if poids_val < 20 or poids_val > 300:
                messages.error(request, "Le poids doit être entre 20 et 300 kg.")
                return _render_form_with_errors(request, athlete, ligue, form_data)
        except (ValueError, TypeError):
            messages.error(request, "Poids invalide.")
            return _render_form_with_errors(request, athlete, ligue, form_data)
        if not medecin_nom:
            messages.error(request, "Veuillez indiquer le nom du médecin.")
            return _render_form_with_errors(request, athlete, ligue, form_data)
        if not date_visite_str:
            messages.error(request, "Veuillez indiquer la date de la visite médicale.")
            return _render_form_with_errors(request, athlete, ligue, form_data)
        if not resultat_global or resultat_global == 'EN_ATTENTE':
            messages.error(request, "Veuillez sélectionner le résultat global de la visite médicale.")
            return _render_form_with_errors(request, athlete, ligue, form_data)
        if resultat_global == 'INAPTE':
            messages.error(request, "L'athlète est déclaré INAPTE. Le dossier reste en attente ; pas de passage en validation.")
            return _render_form_with_errors(request, athlete, ligue, form_data)
        if not certificat_aptitude_delivre:
            messages.error(request, "Le certificat d'aptitude (F72) doit être délivré et coché.")
            return _render_form_with_errors(request, athlete, ligue, form_data)
        # Le certificat PDF est généré par le système (plus besoin d'upload obligatoire)
        if not groupe_sanguin_rh:
            messages.error(request, "Veuillez sélectionner le groupe sanguin et Rhésus.")
            return _render_form_with_errors(request, athlete, ligue, form_data)

        date_visite = datetime.strptime(date_visite_str, '%Y-%m-%d').date() if date_visite_str else timezone.now().date()

        medecin_numero_ordre = (getattr(profil, 'numero_ordre_medecins', None) or '').strip()
        # Créer la visite avec les champs communs ; les examens (ECG, tension, etc.) seront remplis depuis le référentiel
        visite = VisiteMedicale.objects.create(
            athlete=athlete,
            date_visite=date_visite,
            medecin_nom=medecin_nom,
            medecin_etablissement=medecin_etablissement or '',
            medecin_numero_ordre=medecin_numero_ordre,
            recommandations_securite=recommandations_securite,
            resultat_global=resultat_global,
            taille_cm=taille_val,
            poids_kg=poids_val,
            notes_examen_clinique=notes_examen,
            groupe_sanguin_rh=groupe_sanguin_rh,
            certificat_aptitude_joint=None,
            certificat_aptitude_delivre=True,
            demande_surclassement=demande_surclassement,
            radiographie_poignet_joint=radiographie_poignet or None,
            test_greulich_pyle_ok=test_greulich_ok if demande_surclassement else None,
            created_by=profil,
        )
        # Enregistrer les résultats par type d'examen (référentiel) et repasser sur VisiteMedicale pour compatibilité
        resultats_par_code = {}
        for type_ex in TypeExamen.objects.filter(actif=True):
            key_ok = f'resultat_examen_{type_ex.id}'
            key_val = f'valeur_examen_{type_ex.id}'
            key_fichier = f'fichier_examen_{type_ex.id}'
            val_ok = request.POST.get(key_ok)
            valeur_texte = (request.POST.get(key_val) or '').strip()
            fichier = request.FILES.get(key_fichier)
            if val_ok in ('1', '0') or valeur_texte or fichier:
                resultat_ok = True if val_ok == '1' else (False if val_ok == '0' else None)
                ResultatExamenVisite.objects.create(
                    visite_medicale=visite,
                    type_examen=type_ex,
                    resultat_ok=resultat_ok,
                    valeur_texte=valeur_texte or '',
                    fichier=fichier or None,
                )
                resultats_par_code[type_ex.code] = {
                    'resultat_ok': resultat_ok,
                    'valeur_texte': valeur_texte,
                    'fichier': fichier,
                }

        # Remplir les champs VisiteMedicale depuis le référentiel (licence, dossier, etc.)
        if 'ECG' in resultats_par_code:
            r = resultats_par_code['ECG']
            f = r.get('fichier')
            if f and hasattr(f, 'seek'):
                f.seek(0)
            visite.ecg_joint = f
            visite.ecg_normal = r.get('resultat_ok')
        if 'TA' in resultats_par_code and resultats_par_code['TA'].get('valeur_texte'):
            ta = re.match(r'(\d+)\s*[/\s]\s*(\d+)', resultats_par_code['TA']['valeur_texte'])
            if ta:
                s, d = int(ta.group(1)), int(ta.group(2))
                if 80 <= s <= 250:
                    visite.tension_systolique = s
                if 40 <= d <= 150:
                    visite.tension_diastolique = d
        if 'CARDIO' in resultats_par_code:
            visite.aptitude_cardiaque = resultats_par_code['CARDIO'].get('resultat_ok')
        if 'OSTEO' in resultats_par_code:
            visite.examen_osteo_articulaire_ok = resultats_par_code['OSTEO'].get('resultat_ok') if resultats_par_code['OSTEO'].get('resultat_ok') is not None else True
        if 'NFS' in resultats_par_code:
            fnfs = resultats_par_code['NFS'].get('fichier')
            if fnfs and hasattr(fnfs, 'seek'):
                fnfs.seek(0)
            visite.hemogramme_fichier = fnfs
            visite.hemogramme_ok = resultats_par_code['NFS'].get('resultat_ok')
        if 'URINES' in resultats_par_code:
            fur = resultats_par_code['URINES'].get('fichier')
            if fur and hasattr(fur, 'seek'):
                fur.seek(0)
            visite.examen_urines_fichier = fur
            visite.examen_urines_ok = resultats_par_code['URINES'].get('resultat_ok')
        if 'ACU_VIS' in resultats_par_code and resultats_par_code['ACU_VIS'].get('valeur_texte'):
            visite.acuite_visuelle = resultats_par_code['ACU_VIS']['valeur_texte']
        if 'ACU_AUD' in resultats_par_code and resultats_par_code['ACU_AUD'].get('valeur_texte'):
            visite.acuite_auditive = resultats_par_code['ACU_AUD']['valeur_texte']
        # ECG obligatoire pour la licence
        if not visite.ecg_joint or visite.ecg_normal is None:
            messages.error(
                request,
                "L'ECG est obligatoire pour la prévention de la mort subite. Renseignez le type d'examen « Électrocardiogramme (ECG) » avec document et résultat (Conforme/Non conforme)."
            )
            visite.delete()
            return _render_form_with_errors(request, athlete, ligue, form_data)
        visite.save()
        # Générer le certificat d'aptitude (F72) — preuve juridique avec QR code de vérification
        try:
            from django.core.files.base import ContentFile
            from gouvernance.certificat_aptitude_generator import generer_certificat_aptitude_pdf
            base_url = request.build_absolute_uri('/').rstrip('/')
            pdf_buffer = generer_certificat_aptitude_pdf(visite, base_url=base_url)
            filename = f"Certificat_Aptitude_F72_{athlete.numero_sportif}_{visite.date_visite.strftime('%Y%m%d')}.pdf"
            visite.certificat_aptitude_joint.save(filename, ContentFile(pdf_buffer.getvalue()), save=True)
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception("Génération du certificat F72 PDF: %s", e)
            messages.warning(request, "Examen enregistré mais la génération du certificat PDF a échoué. Veuillez contacter l'administrateur.")
        athlete.statut_certification = 'EN_ATTENTE_VALIDATION_LIGUE'
        athlete.resultat_test_medical = resultat_global
        athlete.date_test_medical = date_visite
        athlete.taille = taille_val
        athlete.poids = poids_val
        athlete.groupe_sanguin = groupe_sanguin_rh
        if visite.certificat_aptitude_joint:
            athlete.certificat_medical_enrolement = visite.certificat_aptitude_joint
        athlete.save()
        messages.success(
            request,
            f"Examen médical (F67) enregistré pour {athlete.personne.nom_complet}. Le dossier est en attente de validation par le secrétaire de la ligue."
        )
        return redirect('gouvernance:medecin_athletes_en_attente_examen')

    types_examen = TypeExamen.objects.filter(actif=True).order_by('ordre', 'libelle')
    has_examens_optionnels = any(not te.obligatoire for te in types_examen)
    medecin_nom = ''
    if profil:
        try:
            if getattr(profil, 'agent', None) and profil.agent.personne_id:
                medecin_nom = profil.agent.personne.nom_complet
            elif getattr(profil, 'personne', None) and profil.personne_id:
                medecin_nom = profil.personne.nom_complet
        except Exception:
            pass
    if not medecin_nom and request.user:
        medecin_nom = request.user.get_full_name() or (getattr(request.user, 'email', '') or '')
    has_empreintes_template = False
    try:
        cap = athlete.capture_empreintes
        has_empreintes_template = cap.has_templates
    except CaptureEmpreintes.DoesNotExist:
        pass
    from django.conf import settings
    context = {
        'ligue': ligue,
        'athlete': athlete,
        'types_examen': types_examen,
        'has_examens_optionnels': has_examens_optionnels,
        'medecin_nom': medecin_nom or '',
        'form_data': {},
        'user_role': 'medecin_inspecteur',
        'has_empreintes_template': has_empreintes_template,
        'morpho_service_uri': getattr(settings, 'MORPHO_SERVICE_URI', 'http://localhost:8032/morfinenroll/'),
    }
    return render(request, 'gouvernance/medecin_athlete_examen_medical.html', context)


@login_required
@require_role('MEDECIN_INSPECTEUR')
def medecin_athlete_empreinte_template(request, athlete_uid):
    """
    API JSON : retourne le template d'empreinte (base64) de l'athlète pour la vérification biométrique
    avant l'examen F67. Le client appelle le lecteur Morpho pour capturer une empreinte puis
    MorFinEnrollMatchTemplate(galleryTemplate, probeTemplate) pour comparer.
    """
    import base64
    profil, ligue = _get_medecin_ligue_context(request)
    if not ligue:
        return JsonResponse({'ok': False, 'error': 'Accès non autorisé'}, status=403)
    athlete = get_object_or_404(Athlete, uid=athlete_uid, actif=True)
    if athlete.club.institution_tutelle != ligue:
        return JsonResponse({'ok': False, 'error': 'Athlète hors ligue'}, status=403)
    try:
        capture = athlete.capture_empreintes
    except CaptureEmpreintes.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Aucune empreinte enregistrée pour cet athlète'}, status=404)
    # Premier template disponible (main droite 4 doigts utilisé pour la vérification 1:1)
    template_b64 = None
    for raw in (capture.main_droite_4_template, capture.main_gauche_4_template, capture.pouces_2_template):
        if raw:
            try:
                template_b64 = base64.b64encode(raw).decode('ascii')
                break
            except Exception:
                continue
    if not template_b64:
        return JsonResponse({'ok': False, 'error': 'Templates d\'empreintes absents pour cet athlète'}, status=404)
    return JsonResponse({
        'ok': True,
        'template_base64': template_b64,
        'temp_format': '0',
    })


# ---------- Types d'examens (référentiel) — Médecin Inspecteur peut ajouter/modifier ----------

def _get_medecin_ligue_context_for_types(request):
    """Retourne (profil, ligue) ou (None, None) si accès invalide."""
    try:
        profil = request.user.profil_sisep
    except Exception:
        return None, None
    ligue = profil.institution
    if not ligue or ligue.niveau_territorial not in ('LIGUE', 'LIGUE_PROVINCIALE'):
        return None, None
    return profil, ligue


@login_required
@require_role('MEDECIN_INSPECTEUR')
def medecin_types_examen_list(request):
    """Liste des types d'examens médicaux. Le Médecin Inspecteur peut en ajouter."""
    profil, ligue = _get_medecin_ligue_context_for_types(request)
    if not ligue:
        return redirect('core:home')
    types_examen = TypeExamen.objects.all().order_by('ordre', 'libelle')
    context = {
        'ligue': ligue,
        'types_examen': types_examen,
        'user_role': 'medecin_inspecteur',
    }
    return render(request, 'gouvernance/medecin_types_examen_list.html', context)


@login_required
@require_role('MEDECIN_INSPECTEUR')
def medecin_type_examen_create(request):
    """Création d'un nouveau type d'examen par le Médecin Inspecteur."""
    profil, ligue = _get_medecin_ligue_context_for_types(request)
    if not ligue:
        return redirect('core:home')
    if request.method == 'POST':
        libelle = (request.POST.get('libelle') or '').strip()
        code = (request.POST.get('code') or '').strip()
        description = (request.POST.get('description') or '').strip()
        obligatoire = request.POST.get('obligatoire') == '1'
        accepte_fichier = request.POST.get('accepte_fichier') == '1'
        ordre_raw = request.POST.get('ordre', '0')
        try:
            ordre = int(ordre_raw) if ordre_raw else 0
        except (ValueError, TypeError):
            ordre = 0
        if not libelle:
            messages.error(request, "Le libellé est obligatoire.")
            return redirect('gouvernance:medecin_type_examen_create')
        if code and TypeExamen.objects.filter(code=code).exists():
            messages.error(request, f"Un type d'examen avec le code « {code} » existe déjà.")
            return redirect('gouvernance:medecin_type_examen_create')
        TypeExamen.objects.create(
            libelle=libelle,
            code=code,
            description=description,
            obligatoire=obligatoire,
            ordre=ordre,
            accepte_fichier=accepte_fichier,
            actif=True,
        )
        messages.success(request, f"Type d'examen « {libelle} » créé.")
        return redirect('gouvernance:medecin_types_examen_list')
    context = {
        'ligue': ligue,
        'user_role': 'medecin_inspecteur',
    }
    return render(request, 'gouvernance/medecin_type_examen_form.html', context)


@login_required
@require_role('MEDECIN_INSPECTEUR')
def medecin_type_examen_edit(request, type_examen_id):
    """Modification d'un type d'examen."""
    profil, ligue = _get_medecin_ligue_context_for_types(request)
    if not ligue:
        return redirect('core:home')
    type_examen = get_object_or_404(TypeExamen, pk=type_examen_id)
    if request.method == 'POST':
        libelle = (request.POST.get('libelle') or '').strip()
        code = (request.POST.get('code') or '').strip()
        description = (request.POST.get('description') or '').strip()
        obligatoire = request.POST.get('obligatoire') == '1'
        accepte_fichier = request.POST.get('accepte_fichier') == '1'
        actif = request.POST.get('actif') == '1'
        ordre_raw = request.POST.get('ordre', '0')
        try:
            ordre = int(ordre_raw) if ordre_raw else 0
        except (ValueError, TypeError):
            ordre = 0
        if not libelle:
            messages.error(request, "Le libellé est obligatoire.")
            return redirect('gouvernance:medecin_type_examen_edit', type_examen_id=type_examen_id)
        if code and TypeExamen.objects.filter(code=code).exclude(pk=type_examen.pk).exists():
            messages.error(request, f"Un autre type d'examen avec le code « {code} » existe déjà.")
            return redirect('gouvernance:medecin_type_examen_edit', type_examen_id=type_examen_id)
        type_examen.libelle = libelle
        type_examen.code = code
        type_examen.description = description
        type_examen.obligatoire = obligatoire
        type_examen.accepte_fichier = accepte_fichier
        type_examen.actif = actif
        type_examen.ordre = ordre
        type_examen.save()
        messages.success(request, f"Type d'examen « {libelle} » mis à jour.")
        return redirect('gouvernance:medecin_types_examen_list')
    context = {
        'ligue': ligue,
        'type_examen': type_examen,
        'user_role': 'medecin_inspecteur',
    }
    return render(request, 'gouvernance/medecin_type_examen_form.html', context)
