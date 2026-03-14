"""
URLs pour le module Infrastructures Sportives.
"""
from django.urls import path
from . import views, views_types, views_sg_validation, views_billetterie
from .views_infra_manager import (
    infra_manager_dashboard,
    infra_manager_maintenance,
    infra_manager_reservations,
    infra_manager_photos,
    infra_manager_zones,
    infra_manager_evenements,
)

app_name = 'infrastructures'

urlpatterns = [
    # Infrastructure management
    path('list/', views.infrastructure_list, name='infrastructure_list'),
    path('create/', views.infrastructure_create, name='infrastructure_create'),
    path('<uuid:infrastructure_id>/', views.infrastructure_detail, name='infrastructure_detail'),
    path('<uuid:infrastructure_id>/edit/', views.infrastructure_edit, name='infrastructure_edit'),
    path('<uuid:infrastructure_id>/delete/', views.infrastructure_delete, name='infrastructure_delete'),
    
    # Infrastructure Manager (INFRA_MANAGER role)
    path('manager/dashboard/', infra_manager_dashboard, name='infra_manager_dashboard'),
    path('manager/maintenance/', infra_manager_maintenance, name='infra_manager_maintenance'),
    path('manager/reservations/', infra_manager_reservations, name='infra_manager_reservations'),
    path('manager/photos/', infra_manager_photos, name='infra_manager_photos'),
    path('manager/zones/', infra_manager_zones, name='infra_manager_zones'),
    path('manager/evenements/', infra_manager_evenements, name='infra_manager_evenements'),

    # SG Infrastructure validation
    path('sg/validation/', views_sg_validation.infrastructure_validation_list, name='sg_infrastructure_validation_list'),
    path('sg/validation/<uuid:infrastructure_id>/', views_sg_validation.infrastructure_validation_detail, name='sg_infrastructure_validation_detail'),
    
    # Billetterie — Vérification ticket (QR / UUID) anti-fraude
    path('verifier-ticket/<uuid:ticket_uid>/', views_billetterie.verifier_ticket, name='verifier_ticket'),

    # Type infrastructure management (SG only)
    path('types/', views_types.type_infrastructure_list, name='type_infrastructure_list'),
    path('types/create/', views_types.type_infrastructure_create, name='type_infrastructure_create'),
    path('types/<uuid:type_id>/edit/', views_types.type_infrastructure_edit, name='type_infrastructure_edit'),
    path('types/<uuid:type_id>/delete/', views_types.type_infrastructure_delete, name='type_infrastructure_delete'),
]
