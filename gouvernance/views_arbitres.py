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
@require_role('INSTITUTION_ADMIN', 'MINISTRE', 'FEDERATION_SECRETARY', 'MEDECIN_LIGUE', 'MEDECIN_INSPECTEUR')
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
@require_role('MEDECIN_INSPECTEUR')
def arbitre_verdict_medical(request, uid):
    arbitre = get_object_or_404(Arbitre, uid=uid)

    if arbitre.statut not in ('EN_ATTENTE_MEDICALE',):
        messages.warning(request, "Ce dossier n'est plus en attente d'examen médical.")
        return redirect('gouvernance:arbitres_list')

    # Biométrie obligatoire avant examen médical
    if not arbitre.empreintes_capturees or not arbitre.photo:
        messages.error(request, "La biométrie (photo + empreintes) doit être complétée avant l'examen médical.")
        return redirect('gouvernance:medecin_athletes_en_attente_examen')

    if request.method == 'POST':
        resultat = request.POST.get('resultat_medical', '').strip()
        notes = request.POST.get('notes_medicales', '').strip()
        date_examen_str = request.POST.get('date_examen_medical', '').strip()

        if resultat not in ('APTE', 'INAPTE', 'APTE_AVEC_RESERVE'):
            messages.error(request, "Résultat médical invalide.")
            return render(request, 'gouvernance/arbitre_verdict_medical.html', {
                'arbitre': arbitre,
                'today': timezone.now().date(),
                'steps_workflow': [(1,'Enregistrement',True),(2,'Examen médical',False),(3,'Validation ligue',False)],
            })

        from datetime import datetime as dt
        try:
            date_examen = dt.strptime(date_examen_str, '%Y-%m-%d').date() if date_examen_str else timezone.now().date()
        except ValueError:
            date_examen = timezone.now().date()

        arbitre.resultat_medical = resultat
        arbitre.notes_medicales = notes
        arbitre.date_examen_medical = date_examen

        if resultat in ('APTE', 'APTE_AVEC_RESERVE'):
            arbitre.statut = 'INSTRUIT'
        else:
            arbitre.statut = 'INAPTE'

        arbitre.save()

        # Générer le certificat médical PDF
        try:
            from django.core.files.base import ContentFile
            from gouvernance.certificat_aptitude_generator import generer_certificat_medical_arbitre_pdf
            base_url = request.build_absolute_uri('/').rstrip('/')
            pdf_buffer = generer_certificat_medical_arbitre_pdf(arbitre, base_url=base_url)
            nom_fichier = f"Certificat_Medical_Arbitre_{arbitre.uid}_{date_examen.strftime('%Y%m%d')}.pdf"
            arbitre.certificat_medical.save(nom_fichier, ContentFile(pdf_buffer.getvalue()), save=True)
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception("Génération certificat médical arbitre: %s", e)
            messages.warning(request, "Verdict enregistré mais la génération du certificat PDF a échoué.")

        if resultat in ('APTE', 'APTE_AVEC_RESERVE'):
            messages.success(request, f"Arbitre déclaré {arbitre.get_resultat_medical_display()}. Certificat médical généré. Dossier en attente de validation par la ligue.")
        else:
            messages.warning(request, "Arbitre déclaré inapte. Dossier bloqué.")

        return redirect('gouvernance:arbitres_list')

    return render(request, 'gouvernance/arbitre_verdict_medical.html', {
        'arbitre': arbitre,
        'today': timezone.now().date(),
        'steps_workflow': [
            (1, 'Enregistrement', True),
            (2, 'Examen médical', False),
            (3, 'Validation ligue', False),
        ],
    })


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
@require_role('INSTITUTION_ADMIN', 'MINISTRE', 'FEDERATION_SECRETARY', 'MEDECIN_LIGUE', 'MEDECIN_INSPECTEUR')
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
        # Photos
        if 'photo' in request.FILES:
            arbitre.photo = request.FILES['photo']
        if 'photo_gauche' in request.FILES:
            arbitre.photo_gauche = request.FILES['photo_gauche']
        if 'photo_droite' in request.FILES:
            arbitre.photo_droite = request.FILES['photo_droite']

        # Empreintes — images 4-4-2 (fichier ou base64)
        import base64
        from django.core.files.base import ContentFile

        def save_b64_image(field_name, b64_field_name, filename):
            if field_name in request.FILES:
                setattr(arbitre, field_name, request.FILES[field_name])
            else:
                b64 = request.POST.get(b64_field_name, '').strip()
                if b64:
                    try:
                        data = base64.b64decode(b64)
                        setattr(arbitre, field_name, ContentFile(data, name=filename))
                    except Exception:
                        pass

        def save_b64_template(field_name, b64_field_name):
            b64 = request.POST.get(b64_field_name, '').strip()
            if b64:
                try:
                    setattr(arbitre, field_name, base64.b64decode(b64))
                except Exception:
                    pass

        save_b64_image('main_droite_4', 'main_droite_4_b64', f'empr_droite_{arbitre.uid}.bmp')
        save_b64_image('main_gauche_4', 'main_gauche_4_b64', f'empr_gauche_{arbitre.uid}.bmp')
        save_b64_image('pouces_2',      'pouces_2_b64',      f'empr_pouces_{arbitre.uid}.bmp')

        save_b64_template('main_droite_4_template', 'main_droite_4_template_b64')
        save_b64_template('main_gauche_4_template', 'main_gauche_4_template_b64')
        save_b64_template('pouces_2_template',      'pouces_2_template_b64')

        # Marquer empreintes capturées si les 3 étapes sont présentes
        if arbitre.main_droite_4 and arbitre.main_gauche_4 and arbitre.pouces_2:
            arbitre.empreintes_capturees = True

        # Rétrocompatibilité : ancien champ empreintes_template
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
