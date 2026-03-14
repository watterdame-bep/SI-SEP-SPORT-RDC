from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.utils import timezone
from gouvernance.models import Institution, ClubValidation, TypeInstitution
from gouvernance.models import AdresseContact
from core.permissions import require_role
from core.models import ProfilUtilisateur


def get_or_create_division_provinciale(province_admin):
    """
    Retourne l'Institution « Division provinciale » pour la province donnée.
    Crée l'institution si elle n'existe pas (pour que les ClubValidation puissent exister).
    """
    if not province_admin:
        return None
    code = f'DIV-PROV-{province_admin.uid}'
    type_inst, _ = TypeInstitution.objects.get_or_create(
        code='DIVISION_PROVINCIALE',
        defaults={'designation': 'Division Provinciale'}
    )
    division, created = Institution.objects.get_or_create(
        code=code,
        defaults={
            'nom_officiel': f'Division Provinciale - {province_admin.designation}',
            'type_institution': type_inst,
            'niveau_territorial': 'PROVINCIAL',
            'province_admin': province_admin,
        }
    )
    if not created and division.province_admin_id != province_admin.uid:
        division.province_admin = province_admin
        division.save(update_fields=['province_admin'])
    return division


@login_required
@require_role('DIRECTEUR_PROVINCIAL')
def clubs_en_attente_validation(request):
    """
    List clubs awaiting validation for the provincial director's division.
    Affiche les ClubValidation existantes + crée des ClubValidation pour les clubs
    en attente qui n'en ont pas encore (ex: créés avant qu'une division existe).
    """
    try:
        profil = request.user.profil_sisep
    except Exception:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    if not profil.province_admin:
        return render(request, 'gouvernance/clubs_en_attente_validation.html', {
            'validations': ClubValidation.objects.none(),
            'error': 'Vous n\'êtes pas associé à une province.'
        })
    
    # S'assurer qu'une Institution « Division provinciale » existe pour cette province
    division_institution = get_or_create_division_provinciale(profil.province_admin)
    
    # Clubs en attente sans ClubValidation : créer la validation pour qu'ils apparaissent
    clubs_sans_validation = Institution.objects.filter(
        niveau_territorial='CLUB',
        statut_validation_club='EN_ATTENTE_VALIDATION',
        province_admin=profil.province_admin,
    ).exclude(
        uid__in=ClubValidation.objects.values_list('club_id', flat=True)
    )
    for club in clubs_sans_validation:
        ClubValidation.objects.get_or_create(
            club=club,
            defaults={'division_provinciale': division_institution}
        )
    
    # Toutes les validations pour la province du directeur
    validations = ClubValidation.objects.filter(
        division_provinciale__province_admin=profil.province_admin
    ).select_related('club', 'club__institution_tutelle').order_by('-date_demande')
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        validations = validations.filter(statut=status_filter)
    
    # Calculate statistics
    all_validations = ClubValidation.objects.filter(
        division_provinciale__province_admin=profil.province_admin
    )
    stats = {
        'total': all_validations.count(),
        'en_attente': all_validations.filter(statut='EN_ATTENTE').count(),
        'acceptees': all_validations.filter(statut='ACCEPTEE').count(),
        'rejetees': all_validations.filter(statut='REJETEE').count(),
    }
    
    context = {
        'validations': validations,
        'division': division_institution,
        'status_filter': status_filter,
        'statut_choices': ClubValidation.STATUT_CHOICES,
        'stats': stats,
    }
    return render(request, 'gouvernance/clubs_en_attente_validation.html', context)


@login_required
@require_role('DIRECTEUR_PROVINCIAL')
def club_validation_detail(request, validation_id):
    """
    View and validate a club for the provincial director.
    """
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    validation = get_object_or_404(ClubValidation, uid=validation_id)
    club = validation.club
    
    # Verify the user is the director of the correct division
    if not profil.province_admin:
        messages.error(request, "Vous n'êtes pas associé à une province.")
        return redirect('core:home')
    
    # Check if the club's division matches the user's province
    if validation.division_provinciale.province_admin != profil.province_admin:
        messages.error(request, "Vous n'avez pas accès à cette validation.")
        return redirect('gouvernance:clubs_en_attente_validation')
    
    # Get address if exists
    adresse = AdresseContact.objects.filter(institution=club).first()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'accepter':
            # Check if physical existence is confirmed
            existence_confirmed = request.POST.get('existence_physique_confirmee') == 'on'
            
            # Mark club as validated
            validation.statut = 'ACCEPTEE'
            validation.existence_physique_confirmee = existence_confirmed
            validation.date_validation = timezone.now()
            validation.validee_par = profil
            validation.save()
            
            # Update club status
            club.statut_validation_club = 'VALIDEE_PROVINCIALE'
            club.existence_physique_confirmee = existence_confirmed
            club.save()
            
            messages.success(request, f"✓ Club '{club.nom_officiel}' validé avec succès!")
            return redirect('gouvernance:clubs_en_attente_validation')
        
        elif action == 'rejeter':
            motif = request.POST.get('motif_rejet', '').strip()
            
            if not motif:
                messages.error(request, "Veuillez fournir un motif de rejet.")
                return redirect('gouvernance:club_validation_detail', validation_id=validation_id)
            
            # Mark club as rejected
            validation.statut = 'REJETEE'
            validation.date_validation = timezone.now()
            validation.validee_par = profil
            validation.motif_rejet = motif
            validation.save()
            
            # Update club status
            club.statut_validation_club = 'REJETEE_PROVINCIALE'
            club.save()
            
            messages.success(request, f"✓ Club '{club.nom_officiel}' rejeté.")
            return redirect('gouvernance:clubs_en_attente_validation')
    
    context = {
        'validation': validation,
        'club': club,
        'adresse': adresse,
        'division': validation.division_provinciale,
    }
    
    return render(request, 'gouvernance/club_validation_detail.html', context)
