# -*- coding: utf-8 -*-
"""
Vue pour la liste des infrastructures avec carte intégrée.
"""
from django.shortcuts import render
import json
from infrastructures.models import Infrastructure, TypeInfrastructure
from gouvernance.models.localisation import ProvAdmin


def infrastructure_list_with_map(request):
    """
    Page de liste des infrastructures avec carte intégrée.
    Supporte les filtres : recherche, province, type.
    """
    qs = Infrastructure.objects.filter(
        longitude__isnull=False,
        latitude__isnull=False
    ).select_related(
        'territoire',
        'province_admin',
        'type_infrastructure'
    ).order_by('nom')

    # Filtres
    q = request.GET.get('q', '').strip()
    province_id = request.GET.get('province', '').strip()
    type_id = request.GET.get('type', '').strip()

    if q:
        qs = qs.filter(nom__icontains=q)
    if province_id:
        qs = qs.filter(province_admin__uid=province_id)
    if type_id:
        qs = qs.filter(type_infrastructure__uid=type_id)

    infrastructures = list(qs)

    # Préparer les données JSON pour la carte
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
            'type': infra.type_infrastructure.designation if infra.type_infrastructure else 'Non défini',
        })

    # Listes pour les selects de filtre
    provinces = ProvAdmin.objects.order_by('designation')
    types = TypeInfrastructure.objects.order_by('designation')

    return render(request, 'infrastructures/infra_list_with_map.html', {
        'infrastructures': infrastructures,
        'infrastructures_json': json.dumps(infrastructures_data),
        'total_infrastructures': len(infrastructures_data),
        'provinces': provinces,
        'types': types,
        'q': q,
        'province_id': province_id,
        'type_id': type_id,
    })
