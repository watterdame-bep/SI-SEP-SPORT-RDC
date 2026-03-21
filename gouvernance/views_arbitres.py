# -*- coding: utf-8 -*-
"""
Vues pour la gestion des arbitres — workflow CPA.
Ligue (LIGUE_SECRETARY) : enregistrement + validation finale
Médecin (MEDECIN_LIGUE) : verdict médical
SG / Fédération / Ministre : lecture seule
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from core.permissions import require_role
from gouvernance.models import Institution, DisciplineSport
from gouvernance.models.arbitre import Arbitre
from gouvernance.models.personne import Personne


def _get_institution(request):
    try:
        return request.user.profil_sisep.institution
    except Exception:
        return None


def _get_role(request):
    try:
        return request.user.profil_sisep.role
    except Exception:
        return None


# ─────────────────────────────────────────────
# Liste des arbitres
# ─────────────────────────────────────────────
@login_required
@require_role('INSTITUTION_ADMIN', 'MINISTRE', 'FEDERATION_SECRETARY', 'MEDECIN_LIGUE')
def arbitres_list(request):
    role = _get_role(request)
    institution = _get_institution(request)
    is_ministre = role == 'MINISTRE'
    is_medecin = role == 'MEDECIN_LIGUE'

    # Détecter si c'est un secrétaire de ligue (FEDERATION_SECRETARY sur institution LIGUE)
    is_ligue = (
        role == 'FEDERATION_SECRETARY'
        and institution is not None
        and getattr(institution, 'niveau_territorial', None) == 'LIGUE'
    )

    if is_ministre:
        arbitres = Arbitre.objects.select_related('personne', 'discipline', 'institution')
    elif is_ligue or role in ('INSTITUTION_ADMIN', 'MEDECIN_LIGUE'):
        # Ligue : uniquement ses propres arbitres
        arbitres = Arbitre.objects.select_related(
            'personne', 'discipline', 'institution'
        ).filter(institution=institution)
    elif role == 'FEDERATION_SECRETARY' and institution:
        # Fédération nationale : arbitres de toutes ses ligues
        arbitres = Arbitre.objects.select_related(
            'personne', 'discipline', 'institution'
        ).filter(institution__institution_tutelle=institution)
    else:
        arbitres = Arbitre.objects.none()

    arbitres = arbitres.order_by('personne__nom')

    stats = {
        'total': arbitres.count(),
        'en_attente': arbitres.filter(statut='EN_ATTENTE_MEDICALE').count(),
        'instruits': arbitres.filter(statut='INSTRUIT').count(),
        'actifs': arbitres.filter(statut='ACTIF').count(),
    }

    disciplines = DisciplineSport.objects.filter(actif=True).order_by('designation')

    context = {
        'arbitres': arbitres,
        'stats': stats,
        'disciplines': disciplines,
        'is_ministre': is_ministre,
        'is_medecin': is_medecin,
        'is_ligue': is_ligue,
        # Ne pas écraser user_role — le context processor le gère correctement
    }
    return render(request, 'gouvernance/ministre_arbitres_list.html', context)


# ─────────────────────────────────────────────
# Enregistrement (Ligue Secretary)
# ─────────────────────────────────────────────
@login_required
@require_role('FEDERATION_SECRETARY', 'INSTITUTION_ADMIN')
def arbitre_register(request):
    institution = _get_institution(request)
    if not institution:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')

    # Discipline(s) de la ligue — via sa fédération tutelle
    discipline_ligue = None
    disciplines_ligue = []
    if institution.niveau_territorial == 'LIGUE':
        federation = institution.institution_tutelle
        if federation and federation.disciplines.exists():
            disciplines_ligue = list(federation.disciplines.all())
            if len(disciplines_ligue) == 1:
                discipline_ligue = disciplines_ligue[0]
    # Fallback : toutes les disciplines actives
    if not disciplines_ligue:
        disciplines_ligue = list(DisciplineSport.objects.filter(actif=True).order_by('designation'))

    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        postnom = request.POST.get('postnom', '').strip()
        prenom = request.POST.get('prenom', '').strip()
        sexe = request.POST.get('sexe', '').strip()
        telephone = request.POST.get('telephone', '').strip()
        email = request.POST.get('email', '').strip()
        discipline_uid = request.POST.get('discipline', '').strip()
        niveau = 'PROVINCIAL'  # fixé pour la ligue — arbitres provinciaux uniquement
        categorie = request.POST.get('categorie', 'STAGIAIRE').strip()

        if not nom:
            messages.error(request, "Le nom est obligatoire.")
            return render(request, 'gouvernance/arbitre_register.html', {
                'disciplines': disciplines_ligue,
                'discipline_ligue': discipline_ligue,
                'institution': institution,
            })

        personne = Personne.objects.create(
            nom=nom, postnom=postnom, prenom=prenom,
            sexe=sexe, telephone=telephone, email=email,
        )

        discipline = None
        if discipline_uid:
            try:
                discipline = DisciplineSport.objects.get(uid=discipline_uid)
            except DisciplineSport.DoesNotExist:
                pass
        # Si pas sélectionné et discipline unique de la ligue, l'utiliser
        if not discipline and discipline_ligue:
            discipline = discipline_ligue

        arbitre = Arbitre(
            personne=personne,
            discipline=discipline,
            institution=institution,
            niveau=niveau,
            categorie=categorie,
            statut='EN_ATTENTE_MEDICALE',
        )
        arbitre.save()

        messages.success(request, f"Arbitre {personne.nom_complet} enregistré. Complétez maintenant la biométrie.")
        return redirect('gouvernance:arbitre_detail', uid=arbitre.uid)

    return render(request, 'gouvernance/arbitre_register.html', {
        'disciplines': disciplines_ligue,
        'discipline_ligue': discipline_ligue,
        'institution': institution,
    })


# ─────────────────────────────────────────────
# Verdict médical (Médecin de la ligue)
# ─────────────────────────────────────────────
@login_required
@require_role('MEDECIN_LIGUE')
def arbitre_verdict_medical(request, uid):
    arbitre = get_object_or_404(Arbitre, uid=uid)

    if arbitre.statut not in ('EN_ATTENTE_MEDICALE',):
        messages.warning(request, "Ce dossier n'est plus en attente d'examen médical.")
        return redirect('gouvernance:arbitres_list')

    if request.method == 'POST':
        resultat = request.POST.get('resultat_medical', '').strip()
        notes = request.POST.get('notes_medicales', '').strip()
        date_examen = request.POST.get('date_examen_medical', '').strip() or timezone.now().date()

        if resultat not in ('APTE', 'INAPTE', 'APTE_AVEC_RESERVE'):
            messages.error(request, "Résultat médical invalide.")
            return render(request, 'gouvernance/arbitre_verdict_medical.html', {'arbitre': arbitre})

        arbitre.resultat_medical = resultat
        arbitre.notes_medicales = notes
        arbitre.date_examen_medical = date_examen

        if resultat in ('APTE', 'APTE_AVEC_RESERVE'):
            arbitre.statut = 'INSTRUIT'
            messages.success(request, f"Arbitre déclaré {arbitre.get_resultat_medical_display()}. Dossier instruit — en attente de validation par la ligue.")
        else:
            arbitre.statut = 'INAPTE'
            messages.warning(request, "Arbitre déclaré inapte. Dossier bloqué.")

        arbitre.save()
        return redirect('gouvernance:arbitres_list')

    return render(request, 'gouvernance/arbitre_verdict_medical.html', {'arbitre': arbitre})


# ─────────────────────────────────────────────
# Validation finale + génération licence (Ligue Secretary)
# ─────────────────────────────────────────────
@login_required
@require_role('FEDERATION_SECRETARY', 'INSTITUTION_ADMIN')
def arbitre_valider(request, uid):
    arbitre = get_object_or_404(Arbitre, uid=uid)

    if arbitre.statut != 'INSTRUIT':
        messages.error(request, "Ce dossier ne peut pas être validé (statut incorrect).")
        return redirect('gouvernance:arbitres_list')

    if request.method == 'POST':
        arbitre.statut = 'ACTIF'
        arbitre.numero_licence = arbitre.generer_numero_licence()
        arbitre.save()
        messages.success(request, f"Arbitre validé. Licence générée : {arbitre.numero_licence}")
        return redirect('gouvernance:arbitres_list')

    return render(request, 'gouvernance/arbitre_valider_confirm.html', {'arbitre': arbitre})


# ─────────────────────────────────────────────
# Détail arbitre
# ─────────────────────────────────────────────
@login_required
@require_role('INSTITUTION_ADMIN', 'MINISTRE', 'FEDERATION_SECRETARY', 'MEDECIN_LIGUE')
def arbitre_detail(request, uid):
    arbitre = get_object_or_404(
        Arbitre.objects.select_related('personne', 'discipline', 'institution'),
        uid=uid
    )
    role = _get_role(request)
    institution = _get_institution(request)
    is_ligue = (
        role == 'FEDERATION_SECRETARY'
        and institution is not None
        and getattr(institution, 'niveau_territorial', None) == 'LIGUE'
    )
    context = {
        'arbitre': arbitre,
        'can_biometrie': is_ligue or role == 'INSTITUTION_ADMIN',
        'can_verdict': role == 'MEDECIN_LIGUE' and arbitre.statut == 'EN_ATTENTE_MEDICALE',
        'can_valider': (is_ligue or role == 'INSTITUTION_ADMIN') and arbitre.statut == 'INSTRUIT',
    }
    return render(request, 'gouvernance/arbitre_detail.html', context)


# ─────────────────────────────────────────────
# Biométrie : photo + empreintes
# ─────────────────────────────────────────────
@login_required
@require_role('FEDERATION_SECRETARY', 'INSTITUTION_ADMIN')
def arbitre_biometrie(request, uid):
    arbitre = get_object_or_404(Arbitre, uid=uid)

    if request.method == 'POST':
        # Photo
        if 'photo' in request.FILES:
            arbitre.photo = request.FILES['photo']

        # Empreintes (template base64 envoyé par le capteur JS)
        empreintes_data = request.POST.get('empreintes_template', '').strip()
        if empreintes_data:
            arbitre.empreintes_template = empreintes_data
            arbitre.empreintes_capturees = True

        arbitre.save()
        messages.success(request, "Biométrie enregistrée avec succès.")
        return redirect('gouvernance:arbitre_detail', uid=arbitre.uid)

    return render(request, 'gouvernance/arbitre_biometrie.html', {'arbitre': arbitre})


# ─────────────────────────────────────────────
# Suppression arbitre (Ligue Secretary)
# ─────────────────────────────────────────────
@login_required
@require_role('FEDERATION_SECRETARY', 'INSTITUTION_ADMIN')
def arbitre_supprimer(request, uid):
    arbitre = get_object_or_404(Arbitre, uid=uid)
    if request.method == 'POST':
        nom = arbitre.personne.nom_complet
        arbitre.personne.delete()  # cascade supprime l'arbitre aussi
        messages.success(request, f"Arbitre {nom} supprimé.")
    return redirect('gouvernance:arbitres_list')
