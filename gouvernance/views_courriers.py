"""
Vues pour la gestion des courriers et parapheur électronique.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.utils import timezone
from django.http import FileResponse, JsonResponse

from core.permissions import require_role
from gouvernance.models import Institution


@login_required
@require_role('MINISTRE')
def minister_courriers(request):
    """
    Page "Courriers à Signer" : liste des dossiers en attente de signature.
    """
    from gouvernance.models import DisciplineSport
    
    courriers = Institution.objects.filter(
        statut_signature='ATTENTE_SIGNATURE',
        niveau_territorial='FEDERATION'
    ).select_related(
        'type_institution'
    ).prefetch_related(
        'disciplines'
    ).order_by('-date_demande_agrement', 'nom_officiel')
    
    # Nombre pour le badge dans le sidebar
    nb_courriers_attente = courriers.count()
    
    # Récupérer toutes les disciplines pour le filtre
    disciplines = DisciplineSport.objects.filter(actif=True).order_by('designation')
    
    return render(request, 'gouvernance/minister_courriers.html', {
        'courriers': courriers,
        'disciplines': disciplines,
        'user_role': 'ministre',
        'nb_courriers_attente': nb_courriers_attente,
    })


@login_required
@require_role('MINISTRE')
def parapheur_detail(request, pk):
    """
    Page "Parapheur" : vue détaillée d'un dossier pour examen et signature.
    Affiche aussi les décisions des directeurs provinciaux qui ont inspecté la fédération.
    """
    from gouvernance.models import ValidationFederation
    
    dossier = get_object_or_404(
        Institution.objects.select_related(
            'type_institution'
        ).prefetch_related(
            'disciplines',
            'adresses_contact__groupement_quartier__secteur__territoire__province_admin'
        ),
        pk=pk,
        niveau_territorial='FEDERATION',
        statut_signature='ATTENTE_SIGNATURE'
    )
    
    # Récupérer toutes les validations provinciales pour cette fédération
    validations = ValidationFederation.objects.filter(
        federation=dossier
    ).select_related(
        'province',
        'chef_division'
    ).order_by('-date_validation', 'province__designation')
    
    # Nombre pour le badge dans le sidebar
    nb_courriers_attente = Institution.objects.filter(
        statut_signature='ATTENTE_SIGNATURE',
        niveau_territorial='FEDERATION'
    ).count()
    
    return render(request, 'gouvernance/minister_parapheur.html', {
        'dossier': dossier,
        'validations': validations,
        'user_role': 'ministre',
        'nb_courriers_attente': nb_courriers_attente,
    })


@login_required
@require_role('MINISTRE')
@require_http_methods(['POST'])
def signer_courrier(request, uid):
    """Action Ministre : signer une institution en attente."""
    from gouvernance.arrete_generator import sauvegarder_arrete
    from gouvernance.certificate_generator import generer_certificat_homologation
    from django.utils import timezone
    import uuid
    
    institution = get_object_or_404(Institution, uid=uid)
    if institution.statut_signature != 'ATTENTE_SIGNATURE':
        messages.warning(request, "Cette institution n'est plus en attente de signature.")
        return redirect('gouvernance:minister_courriers')
    
    try:
        with transaction.atomic():
            # Mise à jour du statut
            institution.statut_signature = 'SIGNE'
            institution.statut_validee = True
            institution.statut_activation = 'ACTIVE'
            
            # Génération du numéro d'homologation si pas encore généré
            if not institution.numero_homologation:
                # Format: RDC/MIN-SPORT/FED/YYYY-XXX
                year = timezone.now().year
                # Compter les fédérations signées cette année
                count = Institution.objects.filter(
                    statut_signature='SIGNE',
                    date_signature_arrete__year=year,
                    niveau_territorial='FEDERATION'
                ).count() + 1
                institution.numero_homologation = f"RDC/MIN-SPORT/FED/{year}-{count:03d}"
            
            # Génération automatique de l'Arrêté Ministériel d'Agrément
            sauvegarder_arrete(institution)
            
            # Génération du Certificat d'Homologation Nationale
            certificat_pdf = generer_certificat_homologation(institution)
            institution.document_certificat_homologation.save(
                f"Certificat_{institution.numero_homologation}.pdf",
                certificat_pdf,
                save=False
            )
            institution.date_generation_certificat = timezone.now()
            
            # Sauvegarder avec update_fields pour déclencher le signal
            institution.save(update_fields=[
                'statut_signature',
                'statut_validee',
                'statut_activation',
                'numero_homologation',
                'document_certificat_homologation',
                'date_generation_certificat',
                'numero_arrete',
                'date_signature_arrete',
                'document_arrete',
            ])
            
        messages.success(
            request, 
            f"✓ « {institution.nom_officiel} » a été signée et activée avec succès. "
            f"L'Arrêté Ministériel {institution.numero_arrete} et le Certificat d'Homologation "
            f"{institution.numero_homologation} ont été générés automatiquement."
        )
    except Exception as e:
        messages.error(request, f"Erreur lors de la génération des documents : {str(e)}")
        return redirect('gouvernance:parapheur_detail', pk=uid)
    
    return redirect('gouvernance:minister_courriers')


@login_required
@require_role('MINISTRE')
@require_http_methods(['POST'])
def refuser_courrier(request, uid):
    """Action Ministre : refuser une institution en attente."""
    from django.contrib import messages
    
    institution = get_object_or_404(Institution, uid=uid)
    if institution.statut_signature != 'ATTENTE_SIGNATURE':
        messages.warning(request, "Cette institution n'est plus en attente de signature.")
        return redirect('gouvernance:minister_courriers')
    
    motif_refus = request.POST.get('motif_refus', '').strip()
    
    if not motif_refus:
        messages.error(request, "Le motif du refus est obligatoire.")
        return redirect('gouvernance:parapheur_detail', pk=uid)
    
    try:
        with transaction.atomic():
            # Mettre à jour le statut
            institution.statut_signature = 'REFUSE'
            institution.statut_activation = 'INACTIF'
            institution.save()
            
            # Créer une notification pour le SG
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Trouver le SG (INSTITUTION_ADMIN lié au Ministère)
            from core.models import RoleUtilisateur
            sg_users = User.objects.filter(
                profil_sisep__role=RoleUtilisateur.INSTITUTION_ADMIN,
                profil_sisep__institution__institution_tutelle__isnull=True,
                is_active=True
            )
            
            # Ajouter un message pour chaque SG
            for sg_user in sg_users:
                messages.info(
                    request,
                    f"✗ Notification SG: La fédération « {institution.nom_officiel} » a été refusée. "
                    f"Motif: {motif_refus}"
                )
            
            messages.info(
                request, 
                f"✗ « {institution.nom_officiel} » a été refusée. Motif : {motif_refus}"
            )
    except Exception as e:
        messages.error(request, f"Erreur lors du refus: {str(e)}")
        return redirect('gouvernance:parapheur_detail', pk=uid)
    
    return redirect('gouvernance:minister_courriers')


@login_required
@require_role('MINISTRE')
def profil_ministre(request):
    """
    Page de gestion du profil du Ministre (signature et sceau).
    Modification protégée par mot de passe.
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        password = request.POST.get('password', '').strip()
        
        # Vérifier le mot de passe
        if not request.user.check_password(password):
            messages.error(request, "Mot de passe incorrect. Modification annulée.")
            return render(request, 'gouvernance/profil_ministre.html', {
                'profil': profil,
                'user': request.user,
            }, status=400)
        
        if form_type == 'signature':
            if 'signature_image' in request.FILES:
                file = request.FILES['signature_image']
                
                # Vérifier que c'est un fichier PNG
                if file.content_type != 'image/png' and not file.name.lower().endswith('.png'):
                    messages.error(request, "Seuls les fichiers PNG sont acceptés. Veuillez sélectionner un fichier PNG transparent.")
                    return redirect('gouvernance:profil_ministre')
                
                # Vérifier la taille (max 5MB)
                if file.size > 5 * 1024 * 1024:
                    messages.error(request, "Le fichier est trop volumineux. Taille maximale: 5MB.")
                    return redirect('gouvernance:profil_ministre')
                
                profil.signature_image = file
                profil.save()
                messages.success(request, "✓ Signature téléchargée avec succès!")
            else:
                messages.error(request, "Veuillez sélectionner un fichier.")
        
        elif form_type == 'sceau':
            if 'sceau_image' in request.FILES:
                file = request.FILES['sceau_image']
                
                # Vérifier que c'est un fichier PNG
                if file.content_type != 'image/png' and not file.name.lower().endswith('.png'):
                    messages.error(request, "Seuls les fichiers PNG sont acceptés. Veuillez sélectionner un fichier PNG transparent.")
                    return redirect('gouvernance:profil_ministre')
                
                # Vérifier la taille (max 5MB)
                if file.size > 5 * 1024 * 1024:
                    messages.error(request, "Le fichier est trop volumineux. Taille maximale: 5MB.")
                    return redirect('gouvernance:profil_ministre')
                
                profil.sceau_image = file
                profil.save()
                messages.success(request, "✓ Sceau téléchargé avec succès!")
            else:
                messages.error(request, "Veuillez sélectionner un fichier.")
        
        return redirect('gouvernance:profil_ministre')
    
    return render(request, 'gouvernance/profil_ministre.html', {
        'profil': profil,
        'user': request.user,
    })


@login_required
@require_role('INSTITUTION_ADMIN')
def profil_sg(request):
    """
    Page de gestion du profil du Secrétaire Général (signature et sceau).
    Modification protégée par mot de passe.
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        password = request.POST.get('password', '').strip()
        
        # Vérifier le mot de passe
        if not request.user.check_password(password):
            messages.error(request, "Mot de passe incorrect. Modification annulée.")
            return render(request, 'gouvernance/profil_sg.html', {
                'profil': profil,
                'user': request.user,
            }, status=400)
        
        if form_type == 'signature':
            if 'signature_image' in request.FILES:
                file = request.FILES['signature_image']
                
                # Vérifier que c'est un fichier PNG
                if file.content_type != 'image/png' and not file.name.lower().endswith('.png'):
                    messages.error(request, "Seuls les fichiers PNG sont acceptés. Veuillez sélectionner un fichier PNG transparent.")
                    return redirect('gouvernance:profil_sg')
                
                # Vérifier la taille (max 5MB)
                if file.size > 5 * 1024 * 1024:
                    messages.error(request, "Le fichier est trop volumineux. Taille maximale: 5MB.")
                    return redirect('gouvernance:profil_sg')
                
                profil.signature_image = file
                profil.save()
                messages.success(request, "✓ Signature téléchargée avec succès!")
            else:
                messages.error(request, "Veuillez sélectionner un fichier.")
        
        elif form_type == 'sceau':
            if 'sceau_image' in request.FILES:
                file = request.FILES['sceau_image']
                
                # Vérifier que c'est un fichier PNG
                if file.content_type != 'image/png' and not file.name.lower().endswith('.png'):
                    messages.error(request, "Seuls les fichiers PNG sont acceptés. Veuillez sélectionner un fichier PNG transparent.")
                    return redirect('gouvernance:profil_sg')
                
                # Vérifier la taille (max 5MB)
                if file.size > 5 * 1024 * 1024:
                    messages.error(request, "Le fichier est trop volumineux. Taille maximale: 5MB.")
                    return redirect('gouvernance:profil_sg')
                
                profil.sceau_image = file
                profil.save()
                messages.success(request, "✓ Sceau téléchargé avec succès!")
            else:
                messages.error(request, "Veuillez sélectionner un fichier.")
        
        return redirect('gouvernance:profil_sg')
    
    return render(request, 'gouvernance/profil_sg.html', {
        'profil': profil,
        'user': request.user,
    })


@login_required
@require_role('MINISTRE')
def download_certificat(request, pk):
    """Télécharger le Certificat d'Homologation."""
    institution = get_object_or_404(Institution, pk=pk, niveau_territorial='FEDERATION')
    
    if not institution.document_certificat_homologation:
        messages.error(request, "Le certificat n'est pas disponible.")
        return redirect('gouvernance:federation_detail', pk=pk)
    
    try:
        response = FileResponse(
            institution.document_certificat_homologation.open('rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="{institution.document_certificat_homologation.name}"'
        return response
    except Exception as e:
        messages.error(request, f"Erreur lors du téléchargement : {str(e)}")
        return redirect('gouvernance:federation_detail', pk=pk)


def verifier_certificat(request, numero_homologation):
    """Vérifier l'authenticité d'un certificat via QR code."""
    try:
        institution = Institution.objects.get(
            numero_homologation=numero_homologation,
            niveau_territorial='FEDERATION',
            statut_signature='SIGNE'
        )
        
        # Si c'est une requête AJAX, retourner JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({
                'valide': True,
                'nom_federation': institution.nom_officiel,
                'sigle': institution.sigle,
                'numero_homologation': institution.numero_homologation,
                'date_signature': institution.date_signature_arrete.strftime('%d/%m/%Y') if institution.date_signature_arrete else None,
                'statut': 'Actif',
                'disciplines': [d.designation for d in institution.disciplines.all()]
            })
        
        # Sinon, retourner la page HTML
        return render(request, 'gouvernance/verifier_certificat.html', {
            'institution': institution,
            'valide': True,
        })
    except Institution.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({
                'valide': False,
                'message': 'Certificat non trouvé ou invalide'
            }, status=404)
        
        return render(request, 'gouvernance/verifier_certificat.html', {
            'valide': False,
            'message': 'Certificat non trouvé ou invalide'
        }, status=404)
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({
                'valide': False,
                'message': f'Erreur : {str(e)}'
            }, status=500)
        
        return render(request, 'gouvernance/verifier_certificat.html', {
            'valide': False,
            'message': f'Erreur : {str(e)}'
        }, status=500)
