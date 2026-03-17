# -*- coding: utf-8 -*-
"""
URLs pour le portail public.
"""
from django.urls import path
from . import views
from . import views_callbacks
from . import views_map

app_name = 'public'

urlpatterns = [
    path('', views.home, name='home'),
    path('match/<uuid:uid>/acheter/', views.match_purchase, name='match_purchase'),
    path('match/<uuid:uid>/zone/<uuid:zone_uid>/acheter/', views.zone_purchase, name='zone_purchase'),
    path('paiement/confirmation/', views.payment_confirmation, name='payment_confirmation'),
    path('paiement/traiter/', views.process_payment, name='process_payment'),
    path('paiement/attente/', views.payment_waiting, name='payment_waiting'),
    path('paiement/echec/', views.payment_failed, name='payment_failed'),
    path('paiement/succes/', views.payment_success, name='payment_success'),
    # URLs pour les tickets
    path('ticket/<uuid:ticket_uid>/', views.view_ticket, name='view_ticket'),
    path('mes-tickets/', views.my_tickets, name='my_tickets'),
    path('ticket/<uuid:ticket_uid>/imprimer/', views.print_ticket, name='print_ticket'),
    path('ticket/<uuid:ticket_uid>/telecharger/', views.download_ticket, name='download_ticket'),
    path('vente/<uuid:vente_uid>/telecharger/', views.download_vente, name='download_vente'),
    # URLs pour callbacks et validation
    path('api/callback/mmo/', views_callbacks.mobile_money_callback, name='mobile_money_callback'),
    path('api/paiement/verifier/<str:order_number>/', views_callbacks.verifier_statut_paiement, name='verifier_statut_paiement'),
    path('api/payment/status/', views.payment_status_api, name='payment_status_api'),
    path('api/clear-payment-session/', views.clear_payment_session, name='clear_payment_session'),
    path('api/get-purchase-return-url/', views.get_purchase_return_url, name='get_purchase_return_url'),
    # URL pour la carte
    path('carte/', views_map.map_view, name='map_view'),

    # URL de validation simplifiée
    path('valider-paiement/<uuid:vente_uid>/', views_callbacks.valider_paiement_simplifie, name='valider_paiement_simplifie'),
]
