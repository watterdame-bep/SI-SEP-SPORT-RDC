from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

from core.models import ProfilUtilisateur, RoleUtilisateur
from core.permissions import est_secretaire_general_ministere
from gouvernance.models import Fonction


def _user_passes_test(test_func, login_url=None):
    from django.contrib.auth.views import redirect_to_login
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            return redirect_to_login(request.get_full_path(), login_url=login_url)
        return wrapper
    return decorator


@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
def parametres_fonctions(request):
    """
    Page de paramètres pour gérer les fonctions du ministère.
    Accessible uniquement au Secrétaire Général.
    """
    try:
        profil = request.user.profil_sisep
    except ProfilUtilisateur.DoesNotExist:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    if not profil.institution:
        messages.error(request, "Aucune institution associée à votre profil.")
        return redirect('core:home')
    
    mon_institution = profil.institution
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            designation = request.POST.get('designation', '').strip()
            ordre_priorite = request.POST.get('ordre_priorite', '0')
            
            if not designation:
                messages.error(request, "La désignation de la fonction est requise.")
            else:
                try:
                    ordre_priorite = int(ordre_priorite)
                except ValueError:
                    ordre_priorite = 0
                
                # Vérifier si la fonction existe déjà
                if Fonction.objects.filter(designation__iexact=designation).exists():
                    messages.error(request, f"La fonction '{designation}' existe déjà.")
                else:
                    Fonction.objects.create(
                        designation=designation,
                        ordre_priorite=ordre_priorite
                    )
                    messages.success(request, f"Fonction '{designation}' ajoutée avec succès.")
                    return redirect('parametres:parametres_fonctions')
        
        elif action == 'delete':
            fonction_id = request.POST.get('fonction_id')
            try:
                fonction = Fonction.objects.get(uid=fonction_id)
                # Vérifier si la fonction est utilisée
                if fonction.membres.exists():
                    messages.error(request, f"Impossible de supprimer '{fonction.designation}' - elle est utilisée par des membres.")
                else:
                    designation = fonction.designation
                    fonction.delete()
                    messages.success(request, f"Fonction '{designation}' supprimée avec succès.")
                    return redirect('parametres:parametres_fonctions')
            except Fonction.DoesNotExist:
                messages.error(request, "Fonction non trouvée.")
        
        elif action == 'update':
            fonction_id = request.POST.get('fonction_id')
            designation = request.POST.get('designation', '').strip()
            ordre_priorite = request.POST.get('ordre_priorite', '0')
            
            if not designation:
                messages.error(request, "La désignation de la fonction est requise.")
            else:
                try:
                    ordre_priorite = int(ordre_priorite)
                except ValueError:
                    ordre_priorite = 0
                
                try:
                    fonction = Fonction.objects.get(uid=fonction_id)
                    fonction.designation = designation
                    fonction.ordre_priorite = ordre_priorite
                    fonction.save()
                    messages.success(request, f"Fonction '{designation}' mise à jour avec succès.")
                    return redirect('parametres:parametres_fonctions')
                except Fonction.DoesNotExist:
                    messages.error(request, "Fonction non trouvée.")
    
    # Récupérer toutes les fonctions
    fonctions = Fonction.objects.all().order_by('ordre_priorite', 'designation')
    
    return render(request, 'parametres/parametres_fonctions.html', {
        'mon_institution': mon_institution,
        'fonctions': fonctions,
        'user_role': 'sg',
    })
