# -*- coding: utf-8 -*-
"""
Vues pour la carte interactive des infrastructures.
"""
from django.shortcuts import render
from django.http import JsonResponse
import json
from infrastructures.models import Infrastructure


def map_view(request):
    """
    Page de carte interactive avec OpenStreetMap et Leaflet.
    Affiche les infrastructures sportives de la RD Congo.
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
        'nom', 
        'longitude', 
        'latitude', 
        'capacite_spectateurs',
        'territoire__designation',
        'province_admin__designation',
        'type_infrastructure__designation'
    )
    
    # Préparer les données pour le template
    infrastructures_data = []
    for infra in infrastructures:
        infrastructures_data.append({
            'nom': infra.nom,
            'longitude': float(infra.longitude) if infra.longitude else 0,
            'latitude': float(infra.latitude) if infra.latitude else 0,
            'capacite': int(infra.capacite_spectateurs) if infra.capacite_spectateurs else 0,
            'ville': infra.territoire.designation if infra.territoire else 'Non défini',
            'province': infra.province_admin.designation if infra.province_admin else 'Non défini',
            'type': infra.type_infrastructure.designation if infra.type_infrastructure else 'Non défini'
        })
    
    return render(request, 'map.html', {
        'infrastructures_json': json.dumps(infrastructures_data),
        'total_infrastructures': len(infrastructures_data)
    })
