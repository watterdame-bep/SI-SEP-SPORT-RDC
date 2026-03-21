"""
URLs pour le module Infrastructures Sportives.
"""
from django.urls import path
from . import views, views_types, views_sg_validation, views_billetterie
from . import views_infra_manager
from . import views_infra_list
from .views_infra_manager import (
    infra_manager_dashboard,
    infra_manager_maintenance,
    infra_manager_reservations,
    infra_manager_photos,
    infra_manager_evenements,
)

app_name = 'infrastructures'

urlpatterns = [
    # Infrastructure management
    path('list/', views.infrastructure_list, name='infrastructure_list'),
    path('list-with-map/', views_infra_list.infrastructure_list_with_map, name='infrastructure_list_with_map'),
    path('create/', views.infrastructure_create, name='infrastructure_create'),
    path('<uuid:infrastructure_id>/', views.infrastructure_detail, name='infrastructure_detail'),
    path('<uuid:infrastructure_id>/edit/', views.infrastructure_edit, name='infrastructure_edit'),
    path('<uuid:infrastructure_id>/delete/', views.infrastructure_delete, name='infrastructure_delete'),
    
    # Infrastructure Manager (INFRA_MANAGER role)
    path('manager/dashboard/', infra_manager_dashboard, name='infra_manager_dashboard'),
    path('manager/maintenance/', infra_manager_maintenance, name='infra_manager_maintenance'),
    path('manager/reservations/', infra_manager_reservations, name='infra_manager_reservations'),
    path('manager/photos/', infra_manager_photos, name='infra_manager_photos'),
    path('manager/evenements/', infra_manager_evenements, name='infra_manager_evenements'),

    # SG Infrastructure validation
    path('sg/validation/', views_sg_validation.infrastructure_validation_list, name='sg_infrastructure_validation_list'),
    path('sg/validation/<uuid:infrastructure_id>/', views_sg_validation.infrastructure_validation_detail, name='sg_infrastructure_validation_detail'),
    
    # Billetterie — Vérification ticket (QR / UUID) anti-fraude
    path('verifier-ticket/<uuid:ticket_uid>/', views_billetterie.verifier_ticket, name='verifier_ticket'),
    
    # Billetterie — Gestionnaire d'infrastructure
    path('manager/rencontres/', views_billetterie.infra_manager_rencontres_list, name='infra_manager_rencontres_list'),
    path('manager/rencontres/<uuid:rencontre_uid>/configurer/', views_billetterie.infra_manager_rencontre_configurer_billetterie, name='infra_manager_rencontre_configurer_billetterie'),
    path('manager/rencontres/<uuid:rencontre_uid>/statistiques/', views_billetterie.infra_manager_rencontre_statistiques, name='infra_manager_rencontre_statistiques'),
    path('manager/zones/<uuid:zone_evenement_uid>/detail/', views_billetterie.infra_manager_zone_detail, name='infra_manager_zone_detail'),

    # Type infrastructure management (SG only)
    path('types/', views_types.type_infrastructure_list, name='type_infrastructure_list'),
    path('types/create/', views_types.type_infrastructure_create, name='type_infrastructure_create'),
    path('types/<uuid:type_id>/edit/', views_types.type_infrastructure_edit, name='type_infrastructure_edit'),
    path('types/<uuid:type_id>/delete/', views_types.type_infrastructure_delete, name='type_infrastructure_delete'),
]
