# -*- coding: utf-8 -*-
"""
Configuration Mobile Money pour SI-SEP Sport RDC
À ajouter dans le fichier settings.py principal
"""

# Configuration FlexPay Mobile Money
FLEXPAY_API_URL = os.environ.get('FLEXPAY_API_URL', 'https://backend.flexpay.cd/api/rest/v1/paymentService')
FLEXPAY_CHECK_URL = os.environ.get('FLEXPAY_CHECK_URL', 'https://backend.flexpay.cd/api/rest/v1/check/')
FLEXPAY_BEARER_TOKEN = os.environ.get('FLEXPAY_BEARER_TOKEN', 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJcL2xvZ2luIiwicm9sZXMiOlsiTUVSQ0hBTlQiXSwiZXhwIjoxODI4NDU1ODY4LCJzdWIiOiJkNThhZGZkNzkzNzgzN2I1NTQxNzE5M2QyZTAzNzg2ZSJ9.zR-ldRiNsn-iqOQ-S1_XPrbazyX-OyppZGj_2G3whxc')
FLEXPAY_MERCHANT = os.environ.get('FLEXPAY_MERCHANT', 'SISEP-SPORT')

# URLs pour les callbacks
SITE_URL = os.environ.get('SITE_URL', 'http://127.0.0.1:8000')

# Configuration des médias pour les QR codes
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Configuration du logging pour Mobile Money
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'mobile_money.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'public.mobile_money_integration': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'public.views': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Créer le répertoire de logs si nécessaire
import os
logs_dir = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)
