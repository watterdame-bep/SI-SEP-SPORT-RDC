# -*- coding: utf-8 -*-
"""
URLs pour le portail public.
"""
from django.urls import path
from . import views
from . import views_callbacks

app_name = 'public'

urlpatterns = [
    path('', views.home, name='home'),
    path('match/<uuid:uid>/acheter/', views.match_purchase, name='match_purchase'),
    path('match/<uuid:uid>/zone/<uuid:zone_uid>/acheter/', views.zone_purchase, name='zone_purchase'),
    path('paiement/confirmation/', views.payment_confirmation, name='payment_confirmation'),
    path('paiement/traiter/', views.process_payment, name='process_payment'),
    path('paiement/attente/', views.payment_waiting, name='payment_waiting'),
    path('paiement/succes/', views.payment_success, name='payment_success'),
    # URLs pour callbacks et validation
    path('api/callback/mmo/', views_callbacks.mobile_money_callback, name='mobile_money_callback'),
    path('api/paiement/verifier/<str:order_number>/', views_callbacks.verifier_statut_paiement, name='verifier_statut_paiement'),

    # URL de validation simplifiée
    path('valider-paiement/<uuid:vente_uid>/', views_callbacks.valider_paiement_simplifie, name='valider_paiement_simplifie'),
]
