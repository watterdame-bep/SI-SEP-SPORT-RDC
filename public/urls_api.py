# -*- coding: utf-8 -*-
"""
URLs pour l'API Mobile Money de la billetterie SI-SEP Sport RDC
"""
from django.urls import path
from . import views_api

app_name = 'billetterie_api'

urlpatterns = [
    # API Mobile Money
    path('initier-paiement/', views_api.InitierPaiementView.as_view(), name='initier_paiement'),
    path('verifier-paiement/<str:order_number>/', views_api.VerifierPaiementView.as_view(), name='verifier_paiement'),
    path('callback/mmo/', views_api.MobileMoneyCallbackView.as_view(), name='callback_mmo'),
    
    # Vérification QR
    path('verifier-qr/<str:hash_verification>/', views_api.VerifierQRView.as_view(), name='verifier_qr'),
    path('ticket/<uuid:ticket_uid>/qr/', views_api.TicketQRView.as_view(), name='ticket_qr'),
    
    # Statistiques
    path('statistiques/', views_api.StatistiquesBilletterieView.as_view(), name='statistiques'),
]
