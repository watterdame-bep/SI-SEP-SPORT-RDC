# -*- coding: utf-8 -*-
"""
Vues pour l'Administrateur de la Division Provinciale (Directeur Provincial) :
- Liste des médecins enregistrés (MedecinLigue) dans la province.
- Création de compte pour un médecin déjà enregistré : compte créé inactif, email d'activation envoyé au médecin
  (comme pour le secrétaire de club — le médecin active son compte et définit son mot de passe via le lien).
"""
import re
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse

from core.permissions import require_role
from core.models import ProfilUtilisateur, RoleUtilisateur, EmailVerificationToken
from gouvernance.models import Institution, MedecinLigue

User = get_user_model()


def _slug_username(s):
    """Retourne un slug pour le username (lettres, chiffres, underscores)."""
    s = (s or '').strip().lower()
    s = re.sub(r'[^a-z0-9]+', '_', s)
    return s[:30] or 'user'


@login_required
@require_role('DIRECTEUR_PROVINCIAL')
def division_medecins_list(request):
    """
    Liste des médecins des ligues de la province (enregistrements MedecinLigue).
    Affiche pour chaque médecin : nom, ligue, n° Ordre, et si un compte existe ou non.
    La Division peut « Créer le compte » pour un médecin qui n'en a pas encore.
    """
    try:
        profil = request.user.profil_sisep
    except Exception:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    province = profil.province_admin
    if not province:
        messages.error(request, "Aucune province associée à votre profil.")
        return redirect('core:home')
    ligues_province = Institution.objects.filter(
        niveau_territorial__in=['LIGUE', 'LIGUE_PROVINCIALE'],
        province_admin=province
    ).order_by('nom_officiel')
    medecins = MedecinLigue.objects.filter(
        ligue__in=ligues_province
    ).select_related('ligue', 'agent', 'agent__personne', 'profil_utilisateur').order_by('ligue__nom_officiel', 'agent__personne__nom')
    context = {
        'province': province,
        'ligues_province': ligues_province,
        'medecins': medecins,
        'user_role': 'directeur_provincial',
    }
    return render(request, 'gouvernance/division_medecins_list.html', context)


@login_required
@require_role('DIRECTEUR_PROVINCIAL')
def division_medecin_create_account(request, medecin_ligue_uid):
    """
    Créer un compte SI-SEP pour un médecin déjà enregistré (MedecinLigue).
    Aucun mot de passe ni identifiant saisi par la Division : le compte est créé inactif,
    et un email d'activation est envoyé au médecin (comme pour le secrétaire de club).
    Le médecin clique sur le lien dans l'email pour activer son compte et définir son mot de passe.
    """
    try:
        profil = request.user.profil_sisep
    except Exception:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    province = profil.province_admin
    if not province:
        messages.error(request, "Aucune province associée à votre profil.")
        return redirect('core:home')
    medecin_ligue = get_object_or_404(
        MedecinLigue,
        uid=medecin_ligue_uid,
        ligue__province_admin=province
    )
    if medecin_ligue.profil_utilisateur_id:
        messages.warning(request, "Ce médecin possède déjà un compte.")
        return redirect('gouvernance:division_medecins_list')
    agent = medecin_ligue.agent
    personne = agent.personne
    doctor_email = (personne.email or '').strip()
    if not doctor_email:
        messages.error(
            request,
            "Impossible de créer le compte : l'adresse e-mail du médecin n'est pas renseignée. "
            "Veuillez la compléter dans l'interface de la Ligue (Médecins de la ligue), puis réessayer."
        )
        return redirect('gouvernance:division_medecins_list')
    if request.method == 'POST':
        # Générer un username unique (ex: medecin_dupont_ligue_foot)
        base_username = f"medecin_{_slug_username(personne.nom_complet)}_{_slug_username(medecin_ligue.ligue.sigle or medecin_ligue.ligue.nom_officiel)}"
        username = base_username[:40]
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username[:35]}_{counter}"
            counter += 1
        if User.objects.filter(email=doctor_email).exists():
            messages.error(request, "Un compte existe déjà avec cette adresse e-mail.")
            return redirect('gouvernance:division_medecins_list')
        # Créer l'utilisateur inactif, sans mot de passe (il le définira via le lien d'activation)
        user = User.objects.create_user(
            username=username,
            email=doctor_email,
            is_active=False,
        )
        user.set_unusable_password()
        user.first_name = personne.prenom or ''
        user.last_name = personne.nom or ''
        user.save(update_fields=['first_name', 'last_name'])
        profil_medecin = ProfilUtilisateur.objects.create(
            user=user,
            role=RoleUtilisateur.MEDECIN_INSPECTEUR,
            institution=medecin_ligue.ligue,
            agent=agent,
            numero_ordre_medecins=medecin_ligue.numero_ordre_medecins,
            actif=True,
        )
        medecin_ligue.profil_utilisateur = profil_medecin
        medecin_ligue.save(update_fields=['profil_utilisateur'])
        # Token d'activation (lien valide 7 jours)
        token_obj = EmailVerificationToken.objects.create(user=user)
        activation_url = request.build_absolute_uri(
            reverse('core:verify_email', kwargs={'token': token_obj.token})
        )
        context_email = {
            'medecin_nom': personne.nom_complet,
            'ligue_name': medecin_ligue.ligue.nom_officiel,
            'numero_ordre': medecin_ligue.numero_ordre_medecins,
            'user_email': doctor_email,
            'activation_url': activation_url,
        }
        email_html = render_to_string('emails/medecin_ligue_account_activation.html', context_email)
        try:
            email = EmailMultiAlternatives(
                subject=f"Activation de votre compte — Médecin Inspecteur — {medecin_ligue.ligue.nom_officiel}",
                body="Veuillez consulter la version HTML de cet email.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[doctor_email],
            )
            email.attach_alternative(email_html, "text/html")
            email.send(fail_silently=False)
            messages.success(
                request,
                f"Compte créé pour {personne.nom_complet}. Un email d'activation a été envoyé à {doctor_email}. "
                "Le médecin doit cliquer sur le lien dans l'email pour activer son compte et définir son mot de passe."
            )
        except Exception as e:
            messages.warning(
                request,
                f"Compte créé pour {personne.nom_complet}, mais l'envoi de l'email d'activation a échoué ({e}). "
                "Vous pouvez renvoyer l'email depuis la liste des médecins (à implémenter si besoin)."
            )
        return redirect('gouvernance:division_medecins_list')
    context = {
        'province': province,
        'medecin_ligue': medecin_ligue,
        'personne': personne,
        'doctor_email': doctor_email,
        'user_role': 'directeur_provincial',
    }
    return render(request, 'gouvernance/division_medecin_create_account.html', context)


@login_required
@require_role('DIRECTEUR_PROVINCIAL')
def division_medecin_toggle_actif(request, profil_id):
    """Activer ou désactiver le compte d'un Médecin Inspecteur (même province)."""
    try:
        profil = request.user.profil_sisep
    except Exception:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    province = profil.province_admin
    if not province:
        messages.error(request, "Aucune province associée à votre profil.")
        return redirect('core:home')
    medecin_profil = get_object_or_404(
        ProfilUtilisateur,
        pk=profil_id,
        role=RoleUtilisateur.MEDECIN_INSPECTEUR,
        institution__province_admin=province
    )
    medecin_profil.actif = not medecin_profil.actif
    medecin_profil.save(update_fields=['actif'])
    action = "réactivé" if medecin_profil.actif else "désactivé"
    messages.success(request, f"Compte médecin {medecin_profil.user.get_full_name() or medecin_profil.user.username} {action}.")
    return redirect('gouvernance:division_medecins_list')
