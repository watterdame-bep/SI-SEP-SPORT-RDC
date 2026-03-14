"""
Vues pour la gestion des arrêtés ministériels.
"""
from datetime import datetime
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from core.permissions import require_role
from gouvernance.models import Institution


@login_required
@require_role('MINISTRE')
def minister_arretes(request):
    """
    Page "Arrêtés Signés" : historique des dossiers signés.
    """
    arretes = Institution.objects.filter(
        statut_signature='SIGNE',
        niveau_territorial='FEDERATION'
    ).select_related(
        'type_institution'
    ).prefetch_related(
        'disciplines'
    ).order_by('-date_demande_agrement')
    
    # Nombre pour le badge dans le sidebar
    nb_courriers_attente = Institution.objects.filter(
        statut_signature='ATTENTE_SIGNATURE',
        niveau_territorial='FEDERATION'
    ).count()
    
    return render(request, 'gouvernance/minister_arretes.html', {
        'arretes': arretes,
        'user_role': 'ministre',
        'nb_courriers_attente': nb_courriers_attente,
    })


@login_required
@require_role('MINISTRE')
def download_arrete(request, pk):
    """Télécharger un arrêté."""
    institution = get_object_or_404(Institution, pk=pk)
    
    if not institution.document_arrete:
        return render(request, '404.html', status=404)
    
    from django.http import FileResponse
    return FileResponse(
        institution.document_arrete.open('rb'),
        as_attachment=True,
        filename=f"ARRETE_{institution.sigle}_{institution.date_demande_agrement.year}.pdf"
    )


def verifier_arrete(request, uid):
    """
    Page publique de vérification d'un Arrêté Ministériel via QR Code.
    Accessible sans authentification.
    """
    institution = Institution.objects.filter(
        uid=uid,
        statut_signature='SIGNE',
        niveau_territorial='FEDERATION'
    ).prefetch_related('disciplines').first()
    
    return render(request, 'gouvernance/verifier_arrete.html', {
        'institution': institution,
        'current_year': datetime.now().year,
    })
