"""
Vues pour la gestion des types d'infrastructure (SG uniquement).
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from core.permissions import require_role
from .models import TypeInfrastructure


@login_required
@require_role('INSTITUTION_ADMIN')
def type_infrastructure_list(request):
    """
    Liste des types d'infrastructure.
    Accessible uniquement au Secrétaire Général.
    """
    types = TypeInfrastructure.objects.all().order_by('designation')
    
    context = {
        'types': types,
        'user_role': 'sg',
        'total_infrastructures': sum(t.infrastructures.count() for t in types),
    }
    
    return render(request, 'infrastructures/type_infrastructure_list.html', context)


@login_required
@require_role('INSTITUTION_ADMIN')
def type_infrastructure_create(request):
    """
    Créer un nouveau type d'infrastructure.
    Accessible uniquement au Secrétaire Général.
    """
    if request.method == 'POST':
        designation = request.POST.get('designation', '').strip()
        code = request.POST.get('code', '').strip().upper()
        
        # Validations
        if not designation:
            messages.error(request, "La désignation est requise.")
            return redirect('infrastructures:type_infrastructure_list')
        
        if not code:
            messages.error(request, "Le code est requis.")
            return redirect('infrastructures:type_infrastructure_list')
        
        # Vérifier l'unicité
        if TypeInfrastructure.objects.filter(code=code).exists():
            messages.error(request, f"Un type avec le code '{code}' existe déjà.")
            return redirect('infrastructures:type_infrastructure_list')
        
        # Créer le type
        type_infra = TypeInfrastructure.objects.create(
            designation=designation,
            code=code
        )
        
        messages.success(
            request,
            f"✓ Type d'infrastructure '{type_infra.designation}' créé avec succès!"
        )
        return redirect('infrastructures:type_infrastructure_list')
    
    return render(request, 'infrastructures/type_infrastructure_form.html', {
        'title': 'Créer un Type d\'Infrastructure',
        'user_role': 'sg',
    })


@login_required
@require_role('INSTITUTION_ADMIN')
def type_infrastructure_edit(request, type_id):
    """
    Modifier un type d'infrastructure.
    Accessible uniquement au Secrétaire Général.
    """
    type_infra = get_object_or_404(TypeInfrastructure, uid=type_id)
    
    if request.method == 'POST':
        designation = request.POST.get('designation', '').strip()
        code = request.POST.get('code', '').strip().upper()
        
        # Validations
        if not designation:
            messages.error(request, "La désignation est requise.")
            return redirect('infrastructures:type_infrastructure_list')
        
        if not code:
            messages.error(request, "Le code est requis.")
            return redirect('infrastructures:type_infrastructure_list')
        
        # Vérifier l'unicité (sauf pour le type actuel)
        if TypeInfrastructure.objects.filter(code=code).exclude(uid=type_id).exists():
            messages.error(request, f"Un type avec le code '{code}' existe déjà.")
            return redirect('infrastructures:type_infrastructure_list')
        
        # Mettre à jour
        type_infra.designation = designation
        type_infra.code = code
        type_infra.save()
        
        messages.success(
            request,
            f"✓ Type d'infrastructure '{type_infra.designation}' modifié avec succès!"
        )
        return redirect('infrastructures:type_infrastructure_list')
    
    context = {
        'type_infra': type_infra,
        'title': f'Modifier: {type_infra.designation}',
        'user_role': 'sg',
    }
    
    return render(request, 'infrastructures/type_infrastructure_form.html', context)


@login_required
@require_role('INSTITUTION_ADMIN')
@require_http_methods(["POST"])
def type_infrastructure_delete(request, type_id):
    """
    Supprimer un type d'infrastructure.
    Accessible uniquement au Secrétaire Général.
    """
    type_infra = get_object_or_404(TypeInfrastructure, uid=type_id)
    
    # Vérifier que le type n'est pas utilisé
    if type_infra.infrastructures.exists():
        messages.error(
            request,
            f"Impossible de supprimer '{type_infra.designation}' - "
            f"il est utilisé par {type_infra.infrastructures.count()} infrastructure(s)."
        )
    else:
        designation = type_infra.designation
        type_infra.delete()
        messages.success(
            request,
            f"✓ Type d'infrastructure '{designation}' supprimé avec succès!"
        )
    
    return redirect('infrastructures:type_infrastructure_list')
