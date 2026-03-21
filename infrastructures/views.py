"""
Vues pour le module Infrastructures Sportives.
Gestion des infrastructures par les Secrétaires de Direction Provinciale.
"""
import base64
from io import BytesIO
from PIL import Image

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.http import require_http_methods

from core.permissions import require_role
from .models import Infrastructure, TypeInfrastructure, PhotoInfrastructure
from .forms import InfrastructureForm, PhotoInfrastructureForm


@login_required
def infrastructure_list(request):
    """
    Liste des infrastructures.
    - Directeur Provincial: Voit uniquement les infrastructures de sa province (CRUD complet)
    - Secrétaire Général: Voit toutes les infrastructures du pays (lecture seule)
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    # Déterminer le rôle et les permissions
    is_directeur_provincial = profil.role == 'DIRECTEUR_PROVINCIAL'
    is_sg = profil.role == 'INSTITUTION_ADMIN'
    is_ministre = profil.role == 'MINISTRE'
    
    if not (is_directeur_provincial or is_sg or is_ministre):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Accès refusé. Vous n'avez pas les permissions nécessaires.")
    
    # Récupérer les infrastructures selon le rôle
    if is_directeur_provincial:
        province = profil.province_admin
        if not province:
            messages.error(request, "Aucune province associée à votre profil.")
            return redirect('core:home')
        
        infrastructures = Infrastructure.objects.filter(
            province_admin=province,
            actif=True
        ).select_related('type_infrastructure', 'province_admin').order_by('nom')
        
        user_role = 'directeur_provincial'
    else:  # SG
        # Voir uniquement les infrastructures validées (avec code_homologation)
        infrastructures = Infrastructure.objects.filter(
            actif=True,
            code_homologation__isnull=False
        ).exclude(code_homologation='').select_related('type_infrastructure', 'province_admin').order_by('province_admin__designation', 'nom')
        
        province = None
        user_role = 'sg' if is_sg else 'ministre'
    
    # Filtrage par état de viabilité (optionnel)
    etat_filter = request.GET.get('etat')
    if etat_filter:
        infrastructures = infrastructures.filter(etat_viabilite=etat_filter)
    
    # Filtrage par type de sol (optionnel)
    sol_filter = request.GET.get('sol')
    if sol_filter:
        infrastructures = infrastructures.filter(type_sol=sol_filter)
    
    # Filtrage par province (pour SG et Ministre)
    if is_sg or is_ministre:
        province_filter = request.GET.get('province')
        if province_filter:
            infrastructures = infrastructures.filter(province_admin__uid=province_filter)
    
    # Recherche par nom
    search = request.GET.get('search')
    if search:
        infrastructures = infrastructures.filter(
            Q(nom__icontains=search) | Q(avenue__icontains=search) | Q(quartier__designation__icontains=search)
        )
    
    # Statistiques
    if is_directeur_provincial:
        stats = {
            'total': Infrastructure.objects.filter(province_admin=province, actif=True).count(),
            'operationnels': Infrastructure.objects.filter(
                province_admin=province,
                etat_viabilite='OPERATIONNEL',
                actif=True
            ).count(),
            'en_travaux': Infrastructure.objects.filter(
                province_admin=province,
                etat_viabilite='EN_TRAVAUX',
                actif=True
            ).count(),
            'impraticables': Infrastructure.objects.filter(
                province_admin=province,
                etat_viabilite='IMPRATICABLE',
                actif=True
            ).count(),
        }
    else:  # SG
        stats = {
            'total': Infrastructure.objects.filter(actif=True, code_homologation__isnull=False).exclude(code_homologation='').count(),
            'operationnels': Infrastructure.objects.filter(
                etat_viabilite='OPERATIONNEL',
                actif=True,
                code_homologation__isnull=False
            ).exclude(code_homologation='').count(),
            'en_travaux': Infrastructure.objects.filter(
                etat_viabilite='EN_TRAVAUX',
                actif=True,
                code_homologation__isnull=False
            ).exclude(code_homologation='').count(),
            'impraticables': Infrastructure.objects.filter(
                etat_viabilite='IMPRATICABLE',
                actif=True,
                code_homologation__isnull=False
            ).exclude(code_homologation='').count(),
        }
    
    # Récupérer les provinces pour le filtre SG / Ministre
    provinces = None
    if is_sg or is_ministre:
        from gouvernance.models import ProvAdmin
        provinces = ProvAdmin.objects.all().order_by('designation')
    
    # Compter les infrastructures en attente de validation
    pending_count = 0
    if is_sg:
        pending_count = Infrastructure.objects.filter(
            actif=True,
            code_homologation__isnull=True
        ).count() + Infrastructure.objects.filter(
            actif=True,
            code_homologation=''
        ).count()
    
    # Préparer les données JSON pour la carte Leaflet
    import json
    infrastructures_list = list(infrastructures)
    infrastructures_json = json.dumps([{
        'uid': str(i.uid),
        'nom': i.nom,
        'latitude': float(i.latitude) if i.latitude else 0,
        'longitude': float(i.longitude) if i.longitude else 0,
        'type': i.type_infrastructure.designation if i.type_infrastructure else '—',
        'province': i.province_admin.designation if i.province_admin else '—',
        'capacite': int(i.capacite_spectateurs) if i.capacite_spectateurs else 0,
    } for i in infrastructures_list if i.latitude and i.longitude])

    context = {
        'province': province,
        'infrastructures': infrastructures_list,
        'infrastructures_json': infrastructures_json,
        'stats': stats,
        'etat_choices': Infrastructure.ETAT_VIABILITE_CHOICES,
        'sol_choices': Infrastructure.TYPE_SOL_CHOICES,
        'user_role': user_role,
        'is_directeur_provincial': is_directeur_provincial,
        'is_sg': is_sg,
        'is_ministre': is_ministre,
        'provinces': provinces,
        'pending_count': pending_count if is_sg else 0,
    }
    
    return render(request, 'infrastructures/infrastructure_list.html', context)


@login_required
@require_role('DIRECTEUR_PROVINCIAL')
def infrastructure_create(request):
    """
    Créer une nouvelle infrastructure dans la province.
    Réservé au Directeur Provincial.
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    province = profil.province_admin
    if not province:
        messages.error(request, "Aucune province associée à votre profil.")
        return redirect('core:home')
    
    if request.method == 'POST':
        form = InfrastructureForm(request.POST, user_role='directeur_provincial')
        if form.is_valid():
            infrastructure = form.save(commit=False)
            
            # Assigner la province automatiquement
            infrastructure.province_admin = province
            
            # Générer le code d'homologation si absent
            if not infrastructure.code_homologation:
                # Format: STAD-PROV-XXX (ex: STAD-KIN-001)
                province_code = province.code[:3].upper() if province.code else 'XXX'
                
                # Trouver le prochain numéro disponible
                existing_codes = Infrastructure.objects.filter(
                    code_homologation__startswith=f"STAD-{province_code}-"
                ).values_list('code_homologation', flat=True)
                
                # Extraire les numéros et trouver le max
                numbers = []
                for code in existing_codes:
                    try:
                        num = int(code.split('-')[-1])
                        numbers.append(num)
                    except (ValueError, IndexError):
                        pass
                
                next_num = max(numbers) + 1 if numbers else 1
                infrastructure.code_homologation = f"STAD-{province_code}-{next_num:03d}"
            
            infrastructure.save()
            
            # Handle photo uploads
            photos_data = request.POST.getlist('photos[]')
            if photos_data:
                for idx, photo_data in enumerate(photos_data):
                    if photo_data.startswith('data:image'):
                        # Extract base64 data
                        header, data = photo_data.split(',', 1)
                        image_data = base64.b64decode(data)
                        image = Image.open(BytesIO(image_data))
                        
                        # Save as JPEG
                        output = BytesIO()
                        image.save(output, format='JPEG', quality=80)
                        output.seek(0)
                        
                        # Create PhotoInfrastructure
                        photo = PhotoInfrastructure(
                            infrastructure=infrastructure,
                            description=f'Photo {idx + 1}'
                        )
                        photo.photo.save(
                            f'photo_{idx + 1}.jpg',
                            output,
                            save=True
                        )
            
            messages.success(
                request,
                f"✓ Infrastructure '{infrastructure.nom}' enregistrée avec succès!"
            )
            return redirect('infrastructures:infrastructure_list')
        else:
            # Afficher les erreurs du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = InfrastructureForm(user_role='directeur_provincial')
        # Pre-select the province
        form.initial['province_admin'] = province
    
    context = {
        'form': form,
        'province': province,
        'title': 'Créer une Infrastructure',
        'user_role': 'directeur_provincial',
    }
    
    return render(request, 'infrastructures/infrastructure_form.html', context)


@login_required
@require_role('DIRECTEUR_PROVINCIAL')
def infrastructure_edit(request, infrastructure_id):
    """
    Modifier une infrastructure de la province.
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    province = profil.province_admin
    if not province:
        messages.error(request, "Aucune province associée à votre profil.")
        return redirect('core:home')
    
    # Vérifier que l'infrastructure appartient à la province
    infrastructure = get_object_or_404(
        Infrastructure,
        uid=infrastructure_id,
        province_admin=province
    )
    
    if request.method == 'POST':
        form = InfrastructureForm(request.POST, instance=infrastructure, user_role='directeur_provincial')
        if form.is_valid():
            form.save()
            
            # Handle photo uploads
            photos_data = request.POST.getlist('photos[]')
            if photos_data:
                for idx, photo_data in enumerate(photos_data):
                    if photo_data.startswith('data:image'):
                        # Extract base64 data
                        header, data = photo_data.split(',', 1)
                        image_data = base64.b64decode(data)
                        image = Image.open(BytesIO(image_data))
                        
                        # Save as JPEG
                        output = BytesIO()
                        image.save(output, format='JPEG', quality=80)
                        output.seek(0)
                        
                        # Create PhotoInfrastructure
                        photo = PhotoInfrastructure(
                            infrastructure=infrastructure,
                            description=f'Photo {idx + 1}'
                        )
                        photo.photo.save(
                            f'photo_{idx + 1}.jpg',
                            output,
                            save=True
                        )
            
            messages.success(
                request,
                f"✓ Infrastructure '{infrastructure.nom}' enregistrée avec succès!"
            )
            return redirect('infrastructures:infrastructure_list')
        else:
            # Afficher les erreurs du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = InfrastructureForm(instance=infrastructure, user_role='directeur_provincial')
    
    context = {
        'form': form,
        'infrastructure': infrastructure,
        'province': province,
        'title': f'Modifier: {infrastructure.nom}',
        'user_role': 'directeur_provincial',
    }
    
    return render(request, 'infrastructures/infrastructure_form.html', context)


@login_required
@require_role('DIRECTEUR_PROVINCIAL')
@require_http_methods(["POST"])
def infrastructure_delete(request, infrastructure_id):
    """
    Supprimer une infrastructure de la province.
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    province = profil.province_admin
    if not province:
        messages.error(request, "Aucune province associée à votre profil.")
        return redirect('core:home')
    
    # Vérifier que l'infrastructure appartient à la province
    infrastructure = get_object_or_404(
        Infrastructure,
        uid=infrastructure_id,
        province_admin=province
    )
    
    nom = infrastructure.nom
    infrastructure.delete()
    
    messages.success(
        request,
        f"✓ Infrastructure '{nom}' supprimée avec succès!"
    )
    
    return redirect('infrastructures:infrastructure_list')


@login_required
def infrastructure_detail(request, infrastructure_id):
    """
    Afficher les détails complets d'une infrastructure.
    - Directeur Provincial: Voit uniquement les infrastructures de sa province
    - Secrétaire Général: Voit toutes les infrastructures du pays
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    # Déterminer le rôle et les permissions
    is_directeur_provincial = profil.role == 'DIRECTEUR_PROVINCIAL'
    is_sg = profil.role == 'INSTITUTION_ADMIN'
    is_ministre = profil.role == 'MINISTRE'
    
    if not (is_directeur_provincial or is_sg or is_ministre):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Accès refusé. Vous n'avez pas les permissions nécessaires.")
    
    # Récupérer l'infrastructure selon le rôle
    if is_directeur_provincial:
        province = profil.province_admin
        if not province:
            messages.error(request, "Aucune province associée à votre profil.")
            return redirect('core:home')
        
        infrastructure = get_object_or_404(
            Infrastructure,
            uid=infrastructure_id,
            province_admin=province,
            actif=True
        )
    else:  # SG
        infrastructure = get_object_or_404(
            Infrastructure,
            uid=infrastructure_id,
            actif=True
        )
    
    context = {
        'infrastructure': infrastructure,
        'is_directeur_provincial': is_directeur_provincial,
        'is_sg': is_sg,
        'is_ministre': is_ministre,
        'user_role': 'ministre' if is_ministre else ('sg' if is_sg else 'directeur_provincial'),
    }
    
    return render(request, 'infrastructures/infrastructure_detail.html', context)
