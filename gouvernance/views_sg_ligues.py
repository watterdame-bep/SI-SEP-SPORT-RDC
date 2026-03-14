"""
Vues pour le Secrétaire Général - Gestion des Ligues Provinciales.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q
from django.utils import timezone

from core.permissions import require_role
from gouvernance.models import Institution, ValidationLigue, AttestationReconnaissance


@login_required
@require_role('INSTITUTION_ADMIN')
def sg_ligues_en_attente(request):
    """
    Liste de toutes les Ligues Provinciales pour le SG.
    Affiche les ligues à différents stades de validation.
    """
    # Récupérer TOUTES les ligues (pas seulement celles validées par la Division)
    ligues = Institution.objects.filter(
        niveau_territorial='LIGUE'
    ).select_related(
        'institution_tutelle',
        'province_admin',
        'type_institution'
    ).prefetch_related(
        'validations_division'  # Précharger les validations
    ).order_by('-date_creation')
    
    # Compter les ligues par statut
    nombre_en_inspection = ligues.filter(statut_inspection='EN_INSPECTION').count()
    nombre_attente_sg = ligues.filter(
        statut_inspection='INSPECTION_VALIDEE',
        statut_signature='ATTENTE_SIGNATURE'
    ).count()
    nombre_approuvees = ligues.filter(statut_signature='SIGNE').count()
    nombre_rejetees = ligues.filter(statut_signature='REFUSE').count()
    
    context = {
        'ligues': ligues,
        'nombre_en_inspection': nombre_en_inspection,
        'nombre_attente_sg': nombre_attente_sg,
        'nombre_approuvees': nombre_approuvees,
        'nombre_rejetees': nombre_rejetees,
        'user_role': 'sg',
    }
    
    return render(request, 'gouvernance/sg_ligues_en_attente.html', context)


@login_required
@require_role('INSTITUTION_ADMIN')
def sg_ligue_detail(request, ligue_id):
    """
    Détail d'une ligue avec validation et approbation.
    """
    from gouvernance.models import DivisionProvinciale
    
    ligue = get_object_or_404(
        Institution,
        uid=ligue_id,
        niveau_territorial='LIGUE'
    )
    
    # Récupérer ou créer la validation de la Division
    try:
        validation_division = ValidationLigue.objects.get(ligue=ligue)
    except ValidationLigue.DoesNotExist:
        # Créer la ValidationLigue si elle n'existe pas
        try:
            division_provinciale = DivisionProvinciale.objects.get(
                province=ligue.province_admin
            )
            validation_division = ValidationLigue.objects.create(
                ligue=ligue,
                division_provinciale=division_provinciale,
                statut='EN_ATTENTE_SG'
            )
            messages.info(request, "Dossier de validation créé pour cette ligue.")
        except DivisionProvinciale.DoesNotExist:
            messages.error(
                request, 
                f"Aucune Division Provinciale trouvée pour {ligue.province_admin.designation}. "
                f"Veuillez contacter l'administrateur."
            )
            return redirect('gouvernance:sg_ligues_en_attente')
    
    # Récupérer l'attestation si elle existe
    attestation = AttestationReconnaissance.objects.filter(ligue=ligue).first()
    
    # Récupérer la fédération parente
    federation = ligue.institution_tutelle
    
    # Récupérer les disciplines
    disciplines = ligue.disciplines.all()
    
    context = {
        'ligue': ligue,
        'federation': federation,
        'validation_division': validation_division,
        'attestation': attestation,
        'disciplines': disciplines,
        'user_role': 'sg',
    }
    
    return render(request, 'gouvernance/sg_ligue_detail.html', context)


@login_required
@require_role('INSTITUTION_ADMIN')
@require_http_methods(["POST"])
def sg_approuver_ligue(request, ligue_id):
    """
    Approuver une ligue et générer l'attestation de reconnaissance.
    Crée un compte pour la ligue avec token de vérification email.
    Envoie une notification email à la ligue avec l'attestation en pièce jointe.
    """
    from gouvernance.models import DivisionProvinciale
    from django.core.mail import EmailMessage
    from django.template.loader import render_to_string
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from core.models import ProfilUtilisateur, EmailVerificationToken
    
    User = get_user_model()
    
    ligue = get_object_or_404(
        Institution,
        uid=ligue_id,
        niveau_territorial='LIGUE'
    )
    
    # Vérifier que la ligue est en attente
    if ligue.statut_signature != 'ATTENTE_SIGNATURE':
        messages.error(request, "Cette ligue n'est pas en attente d'approbation.")
        return redirect('gouvernance:sg_ligue_detail', ligue_id=ligue_id)
    
    # Récupérer ou créer la validation de la Division
    try:
        validation_division = ValidationLigue.objects.get(ligue=ligue)
    except ValidationLigue.DoesNotExist:
        try:
            division_provinciale = DivisionProvinciale.objects.get(
                province=ligue.province_admin
            )
            validation_division = ValidationLigue.objects.create(
                ligue=ligue,
                division_provinciale=division_provinciale,
                statut='EN_ATTENTE_SG'
            )
        except DivisionProvinciale.DoesNotExist:
            messages.error(request, "Validation de la Division non trouvée.")
            return redirect('gouvernance:sg_ligues_en_attente')
    
    # Vérifier que la Division a validé
    if validation_division.statut != 'INSPECTION_VALIDEE':
        messages.error(request, "La Division Provinciale n'a pas validé cette ligue.")
        return redirect('gouvernance:sg_ligue_detail', ligue_id=ligue_id)
    
    # Récupérer les observations du SG
    observations_sg = request.POST.get('observations_sg', '').strip()
    
    # Créer ou récupérer l'attestation
    attestation, created = AttestationReconnaissance.objects.get_or_create(
        ligue=ligue,
        validation_division=validation_division,
        defaults={'statut': 'EN_ATTENTE'}
    )
    
    # Générer le numéro d'attestation
    year = timezone.now().year
    province_code = ligue.province_admin.code if ligue.province_admin else 'XX'
    count = AttestationReconnaissance.objects.filter(
        ligue__province_admin=ligue.province_admin,
        date_approbation__year=year
    ).count() + 1
    
    numero_attestation = f"RDC/MIN-SPORT/LIGUE/{province_code}/{year}-{count:03d}"
    
    # Approuver l'attestation et stocker les observations
    attestation.observations_sg = observations_sg
    attestation.approuver(numero_attestation)
    
    # Générer le document d'attestation d'homologation
    attestation_pdf = None
    try:
        from gouvernance.certificate_generator import generer_attestation_homologation_ligue
        attestation_pdf = generer_attestation_homologation_ligue(ligue)
        
        # Sauvegarder le PDF dans le dossier media
        from django.core.files.storage import default_storage
        pdf_filename = f"institutions/attestations/Attestation_Homologation_Ligue_{numero_attestation}.pdf"
        attestation.document_attestation = default_storage.save(pdf_filename, attestation_pdf)
        attestation.save()
    except Exception as e:
        print(f"Erreur lors de la génération du document d'attestation: {e}")
        import traceback
        traceback.print_exc()
    
    # Mettre à jour le statut de la ligue
    ligue.statut_signature = 'SIGNE'
    ligue.save()
    
    # ===== CRÉER UN COMPTE POUR LE SECRÉTAIRE DE LA LIGUE =====
    user_created = False
    verification_token = None
    
    try:
        # Vérifier si un compte existe déjà
        existing_user = User.objects.filter(email=ligue.email_officiel).first()
        
        if not existing_user:
            # Créer un nouvel utilisateur pour le secrétaire de la ligue
            username = ligue.sigle.lower().replace(' ', '_') if ligue.sigle else f"ligue_{ligue.uid}"
            
            # Vérifier que le username est unique
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}_{counter}"
                counter += 1
            
            user = User.objects.create_user(
                username=username,
                email=ligue.email_officiel,
                is_active=False  # Inactif jusqu'à vérification email
            )
            
            # Créer le profil utilisateur pour le secrétaire de la ligue
            profil = ProfilUtilisateur.objects.create(
                user=user,
                institution=ligue,
                role='FEDERATION_SECRETARY'  # Rôle de secrétaire de ligue
            )
            
            # Créer le token de vérification email
            verification_token = EmailVerificationToken.objects.create(user=user)
            
            user_created = True
            print(f"✓ Compte créé pour le secrétaire de la ligue: {username}")
        else:
            # Compte existe déjà, récupérer ou créer le token
            if hasattr(existing_user, 'email_verification_token'):
                verification_token = existing_user.email_verification_token
            else:
                verification_token = EmailVerificationToken.objects.create(user=existing_user)
            print(f"✓ Compte existant trouvé pour: {existing_user.username}")
    except Exception as e:
        print(f"Erreur lors de la création du compte: {e}")
        import traceback
        traceback.print_exc()
    
    # Envoyer email uniquement à la ligue avec pièce jointe
    try:
        recipients = []
        
        # Ajouter l'email de la ligue uniquement
        if ligue.email_officiel:
            recipients.append(ligue.email_officiel)
        
        # Envoyer l'email si au moins un destinataire existe
        if recipients:
            subject = f"Approbation de la Ligue Provinciale - {ligue.nom_officiel}"
            
            # Construire l'URL d'activation
            activation_url = None
            if verification_token:
                site_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
                activation_url = f"{site_url}/verify-email/{verification_token.token}/"
            
            context = {
                'ligue': ligue,
                'federation': ligue.institution_tutelle,
                'numero_attestation': numero_attestation,
                'observations': observations_sg,
                'decision': 'APPROUVEE',
                'verification_token': verification_token.token if verification_token else None,
                'user_created': user_created,
                'activation_url': activation_url,
                'has_activation_link': activation_url is not None,
            }
            html_message = render_to_string('emails/ligue_decision.html', context)
            
            # Créer le message email avec pièce jointe
            email = EmailMessage(
                subject=subject,
                body=html_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@sisep-sport.rdc'),
                to=recipients
            )
            email.content_subtype = 'html'
            
            # Attacher le PDF si disponible
            if attestation.document_attestation:
                try:
                    # Ouvrir le fichier et l'attacher
                    with attestation.document_attestation.open('rb') as pdf_file:
                        email.attach(
                            f'Attestation_Homologation_{numero_attestation}.pdf',
                            pdf_file.read(),
                            'application/pdf'
                        )
                except Exception as e:
                    print(f"Erreur lors de l'attachement du PDF: {e}")
            
            # Envoyer l'email
            email.send(fail_silently=True)
    except Exception as e:
        print(f"Erreur lors de l'envoi d'email: {e}")
        import traceback
        traceback.print_exc()
    
    messages.success(
        request,
        f"Ligue '{ligue.nom_officiel}' approuvée avec succès. "
        f"Numéro d'attestation: {numero_attestation}. "
        f"Notification envoyée à la ligue avec l'attestation en pièce jointe."
    )
    
    return redirect('gouvernance:sg_ligue_detail', ligue_id=ligue_id)


@login_required
@require_role('INSTITUTION_ADMIN')
@require_http_methods(["POST"])
def sg_rejeter_ligue(request, ligue_id):
    """
    Rejeter une ligue et l'attestation.
    Envoie une notification email à la fédération avec les observations du SG.
    """
    from gouvernance.models import DivisionProvinciale
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    
    ligue = get_object_or_404(
        Institution,
        uid=ligue_id,
        niveau_territorial='LIGUE'
    )
    
    # Récupérer les observations du SG
    observations_sg = request.POST.get('observations_sg', '').strip()
    
    # Vérifier que la ligue est en attente
    if ligue.statut_signature != 'ATTENTE_SIGNATURE':
        messages.error(request, "Cette ligue n'est pas en attente d'approbation.")
        return redirect('gouvernance:sg_ligue_detail', ligue_id=ligue_id)
    
    # Récupérer ou créer la validation de la Division
    try:
        validation_division = ValidationLigue.objects.get(ligue=ligue)
    except ValidationLigue.DoesNotExist:
        try:
            division_provinciale = DivisionProvinciale.objects.get(
                province=ligue.province_admin
            )
            validation_division = ValidationLigue.objects.create(
                ligue=ligue,
                division_provinciale=division_provinciale,
                statut='EN_ATTENTE_SG'
            )
        except DivisionProvinciale.DoesNotExist:
            messages.error(request, "Validation de la Division non trouvée.")
            return redirect('gouvernance:sg_ligues_en_attente')
    
    # Créer ou récupérer l'attestation
    attestation, created = AttestationReconnaissance.objects.get_or_create(
        ligue=ligue,
        validation_division=validation_division,
        defaults={'statut': 'EN_ATTENTE'}
    )
    
    # Rejeter l'attestation et stocker les observations
    attestation.observations_sg = observations_sg
    attestation.rejeter()
    
    # Mettre à jour le statut de la ligue
    ligue.statut_signature = 'REFUSE'
    ligue.save()
    
    # Envoyer email de rejet à la ligue uniquement
    try:
        if ligue.email_officiel:
            subject = f"Rejet de la Ligue Provinciale - {ligue.nom_officiel}"
            context = {
                'ligue': ligue,
                'federation': ligue.institution_tutelle,
                'observations': observations_sg,
                'decision': 'REJETEE'
            }
            html_message = render_to_string('emails/ligue_decision.html', context)
            send_mail(
                subject,
                f"La ligue {ligue.nom_officiel} a été rejetée.",
                'noreply@sisep-sport.rdc',
                [ligue.email_officiel],
                html_message=html_message,
                fail_silently=True
            )
    except Exception as e:
        print(f"Erreur lors de l'envoi d'email: {e}")
    
    messages.warning(
        request,
        f"Ligue '{ligue.nom_officiel}' rejetée. "
        f"Notification envoyée à la ligue."
    )
    
    return redirect('gouvernance:sg_ligues_en_attente')


@login_required
@require_role('INSTITUTION_ADMIN')
@require_http_methods(["POST"])
def sg_transferer_ligue_division(request, ligue_id):
    """
    Transférer une ligue à la Division Provinciale pour inspection.
    """
    from gouvernance.models import DivisionProvinciale
    
    ligue = get_object_or_404(
        Institution,
        uid=ligue_id,
        niveau_territorial='LIGUE'
    )
    
    # Vérifier que la ligue est en attente SG
    if ligue.statut_inspection != 'EN_INSPECTION':
        messages.error(request, "Cette ligue n'est pas en attente de transfert.")
        return redirect('gouvernance:sg_ligue_detail', ligue_id=ligue_id)
    
    # Récupérer ou créer la validation de la Division
    try:
        validation_division = ValidationLigue.objects.get(ligue=ligue)
    except ValidationLigue.DoesNotExist:
        try:
            division_provinciale = DivisionProvinciale.objects.get(
                province=ligue.province_admin
            )
            validation_division = ValidationLigue.objects.create(
                ligue=ligue,
                division_provinciale=division_provinciale,
                statut='EN_ATTENTE_SG'
            )
        except DivisionProvinciale.DoesNotExist:
            messages.error(
                request,
                f"Aucune Division Provinciale trouvée pour {ligue.province_admin.designation}. "
                f"Veuillez contacter l'administrateur."
            )
            return redirect('gouvernance:sg_ligues_en_attente')
    
    # Transférer à la Division Provinciale
    validation_division.transferer_a_division(request.user.profil_sisep)
    
    messages.success(
        request,
        f"Ligue '{ligue.nom_officiel}' transférée à la Division Provinciale pour inspection."
    )
    
    return redirect('gouvernance:sg_ligue_detail', ligue_id=ligue_id)
