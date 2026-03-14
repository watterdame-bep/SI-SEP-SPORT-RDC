"""
Vues pour la validation des fédérations par les Directeurs Provinciaux
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.db import transaction

from gouvernance.models import ValidationFederation, Institution
from core.permissions import require_role


@login_required(login_url='/login/')
@require_role('DIRECTEUR_PROVINCIAL')
def validation_detail(request, uid):
    """
    Détail d'une validation de fédération pour inspection
    """
    # Récupérer la province du Directeur Provincial
    try:
        profil = request.user.profil_sisep
        province = profil.province_admin
        if not province:
            return redirect('gouvernance:directeur_provincial_dashboard')
    except:
        return redirect('gouvernance:directeur_provincial_dashboard')
    
    # Récupérer la validation (vérifier que c'est pour la province du Directeur)
    validation = get_object_or_404(
        ValidationFederation.objects.select_related(
            'federation',
            'province',
            'chef_division'
        ),
        uid=uid,
        province=province
    )
    
    context = {
        'validation': validation,
        'federation': validation.federation,
        'province': province,
        'user_role': 'directeur_provincial',
    }
    
    return render(request, 'gouvernance/validation_federation_detail.html', context)


@login_required(login_url='/login/')
@require_role('DIRECTEUR_PROVINCIAL')
@require_http_methods(["POST"])
def validation_submit(request, uid):
    """
    Soumettre la validation d'une fédération (valider ou rejeter)
    """
    try:
        # Récupérer la province du Directeur Provincial
        profil = request.user.profil_sisep
        province = profil.province_admin
        if not province:
            return JsonResponse({
                'success': False,
                'message': 'Vous n\'êtes pas associé à une province'
            }, status=403)
        
        # Récupérer la validation
        validation = get_object_or_404(
            ValidationFederation,
            uid=uid,
            province=province
        )
        
        # Récupérer les données du formulaire
        action = request.POST.get('action', '').strip().lower()  # 'valider' ou 'rejeter'
        existence_physique = request.POST.get('existence_physique') == 'on'
        activite_reelle = request.POST.get('activite_reelle') == 'on'
        conformite_dirigeants = request.POST.get('conformite_dirigeants') == 'on'
        observations = request.POST.get('observations', '').strip()
        
        if action not in ['valider', 'rejeter']:
            return JsonResponse({
                'success': False,
                'message': 'Action invalide'
            }, status=400)
        
        with transaction.atomic():
            # Mettre à jour la validation
            validation.existence_physique = existence_physique
            validation.activite_reelle = activite_reelle
            validation.conformite_dirigeants = conformite_dirigeants
            validation.observations = observations
            validation.chef_division = profil.agent  # Assigner le Chef de Division
            
            if action == 'valider':
                # Vérifier que tous les critères sont cochés
                if not (existence_physique and activite_reelle and conformite_dirigeants):
                    return JsonResponse({
                        'success': False,
                        'message': 'Tous les critères doivent être validés pour approuver'
                    }, status=400)
                
                validation.marquer_comme_validee()
                message = f'Validation approuvée pour {validation.federation.nom_officiel} dans {province.designation}'
            else:  # rejeter
                validation.marquer_comme_rejetee()
                message = f'Validation rejetée pour {validation.federation.nom_officiel} dans {province.designation}'
            
            # NE PAS mettre à jour le statut de la fédération ici
            # Seul le SG peut transférer au Ministre via la vue validation_transfer_to_minister
            # La fédération reste en EN_INSPECTION jusqu'à ce que le SG la transfère
            
            return JsonResponse({
                'success': True,
                'message': message,
                'redirect_url': f'/gouvernance/dashboard/directeur-provincial/'
            })
        
    except ValidationFederation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Validation non trouvée'
        }, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de la validation: {str(e)}'
        }, status=500)


@login_required(login_url='/login/')
@require_role('INSTITUTION_ADMIN')
def sg_validation_verifier(request, uid):
    """
    Vue lecture seule pour le SG : consulter une inspection validée par la direction provinciale
    avant de la transférer au Ministre. Affiche le même détail que le Directeur Provincial.
    """
    validation = get_object_or_404(
        ValidationFederation.objects.select_related(
            'federation',
            'province',
            'chef_division__personne',
        ),
        uid=uid,
    )
    if validation.statut not in ('VALIDEE', 'REJETEE'):
        return redirect('gouvernance:sg_dashboard')
    if validation.federation.statut_inspection != 'EN_INSPECTION':
        return redirect('gouvernance:sg_dashboard')
    context = {
        'validation': validation,
        'federation': validation.federation,
        'province': validation.province,
        'user_role': 'sg',
        'sg_verifier': True,
    }
    return render(request, 'gouvernance/validation_federation_detail.html', context)


@login_required(login_url='/login/')
@require_role('INSTITUTION_ADMIN')
@require_http_methods(["POST"])
def validation_transfer_to_minister(request, uid):
    """
    Transférer une validation complétée au Ministre (SG only)
    """
    try:
        # Récupérer la validation
        validation = get_object_or_404(
            ValidationFederation.objects.select_related('federation'),
            uid=uid
        )
        
        # Vérifier que la validation est complétée (pas EN_ATTENTE)
        if validation.statut == 'EN_ATTENTE':
            return JsonResponse({
                'success': False,
                'message': 'Cette validation n\'a pas encore été inspectée'
            }, status=400)
        
        federation = validation.federation
        
        with transaction.atomic():
            # Mettre à jour le statut de la fédération
            if validation.statut == 'VALIDEE':
                # Inspection approuvée → transférer au Ministre
                federation.statut_inspection = 'INSPECTION_VALIDEE'
                federation.statut_signature = 'ATTENTE_SIGNATURE'
                message = f'{federation.nom_officiel} a été transférée au Ministre pour signature'
            else:  # REJETEE
                # Inspection rejetée → marquer comme rejetée
                federation.statut_inspection = 'INSPECTION_REJETEE'
                federation.statut_signature = 'REFUSE'
                message = f'{federation.nom_officiel} a été rejetée suite à l\'inspection'
            
            federation.save(update_fields=['statut_inspection', 'statut_signature'])
            
            return JsonResponse({
                'success': True,
                'message': message,
                'redirect_url': '/gouvernance/dashboard/sg/'
            })
        
    except ValidationFederation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Validation non trouvée'
        }, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors du transfert: {str(e)}'
        }, status=500)
