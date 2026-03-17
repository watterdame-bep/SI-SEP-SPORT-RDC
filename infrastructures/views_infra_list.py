# -*- coding: utf-8 -*-
"""
Vue pour la liste des infrastructures avec carte intégrée.
"""
from django.shortcuts import render
from django.http import JsonResponse
import json
from infrastructures.models import Infrastructure


def infrastructure_list_with_map(request):
    """
    Page de liste des infrastructures avec carte intégrée.
    Affiche la liste et permet de basculer vers la vue carte.
    """
    # Récupérer toutes les infrastructures avec coordonnées
    infrastructures = Infrastructure.objects.filter(
        longitude__isnull=False,
        latitude__isnull=False
    ).select_related(
        'territoire', 
        'province_admin', 
        'type_infrastructure'
    ).only(
        'uid',
        'nom', 
        'longitude', 
        'latitude', 
        'capacite_spectateurs',
        'territoire__designation',
        'province_admin__designation',
        'type_infrastructure__designation'
    ).order_by('nom')
    
    # Préparer les données pour le template
    infrastructures_data = []
    for infra in infrastructures:
        infrastructures_data.append({
            'uid': str(infra.uid),
            'nom': infra.nom,
            'longitude': float(infra.longitude) if infra.longitude else 0,
            'latitude': float(infra.latitude) if infra.latitude else 0,
            'capacite': int(infra.capacite_spectateurs) if infra.capacite_spectateurs else 0,
            'ville': infra.territoire.designation if infra.territoire else 'Non défini',
            'province': infra.province_admin.designation if infra.province_admin else 'Non défini',
            'type': infra.type_infrastructure.designation if infra.type_infrastructure else 'Non défini'
        })
    
    return render(request, 'infrastructures/infra_list_with_map.html', {
        'infrastructures': infrastructures,
        'infrastructures_json': json.dumps(infrastructures_data),
        'total_infrastructures': len(infrastructures_data)
    })
