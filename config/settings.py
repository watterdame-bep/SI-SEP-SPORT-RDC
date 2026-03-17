"""
SI-SEP Sport RDC - Configuration Django
Système Intégré de Suivi-Évaluation et Pilotage du Sport en RD Congo
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Charger .env si présent
if (BASE_DIR / '.env').exists():
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')

# Limite requête POST (empreintes en base64) — doit être chargé tôt pour éviter RequestDataTooBig
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100 Mo
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100 Mo

SECRET_KEY = os.environ.get('SECRET_KEY', os.environ.get('DJANGO_SECRET_KEY', 'dev-change-me-in-production'))

DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'gouvernance',
    'infrastructures',
    'core',
    'referentiel_geo',
    'parametres',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Dossier templates à la racine
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.user_role',
                'core.context_processors.athletes_counts',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Base de données MySQL — "si-sep sport"
# Créer la base si besoin : CREATE DATABASE `si-sep sport` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'si-sep sport'),
        'USER': os.environ.get('DB_USER', 'root'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Kinshasa'
USE_I18N = True
USE_TZ = True

# URL du site (pour génération de liens absolus, QR codes, etc.)
SITE_URL = os.environ.get('SITE_URL', 'http://127.0.0.1:8000')

# Service Morpho (lecteur d'empreintes) — utilisé côté client pour la capture 4-4-2
MORPHO_SERVICE_URI = os.environ.get('MORPHO_SERVICE_URI', 'http://localhost:8032/morfinenroll/')

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
_static_dirs = [BASE_DIR / 'public', BASE_DIR / 'licence_fichier']
STATICFILES_DIRS = [d for d in _static_dirs if d.exists()]

# Fichiers uploadés (photos, documents)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Envoi d’envoi des requêtes (empreintes en base64 : 3 images + 3 templates peuvent dépasser 2,5 Mo)
# Envoi d'e-mails (SMTP Gmail)
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'dev.jconsult@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'ndlfauwjttiabfim')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'SI-SEP Sport <dev.jconsult@gmail.com>')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'

# Session / cookies — évite les boucles de redirection (ex. Firefox « redirigée incorrectement »)
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = False  # True en production avec HTTPS
SESSION_COOKIE_PATH = '/'

# Configuration des iframe pour autoriser l'affichage dans le dashboard
X_FRAME_OPTIONS = 'SAMEORIGIN'  # Autorise les iframe du même domaine
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False

# Connexion par e-mail ou par nom d'utilisateur
AUTHENTICATION_BACKENDS = [
    'core.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# CORS (à restreindre en production)
CORS_ALLOW_ALL_ORIGINS = DEBUG

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
}

# FlexPay API configuration pour Mobile Money
FLEXPAY_API_URL = os.environ.get(
    'FLEXPAY_API_URL',
    'https://backend.flexpay.cd/api/rest/v1/paymentService'
)
FLEXPAY_CHECK_URL = os.environ.get(
    'FLEXPAY_CHECK_URL',
    'https://backend.flexpay.cd/api/rest/v1/check/'
)
FLEXPAY_BEARER_TOKEN = os.environ.get(
    'FLEXPAY_BEARER_TOKEN',
    'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJcL2xvZ2luIiwicm9sZXMiOlsiTUVSQ0hBTlQiXSwiZXhwIjoxODI4NDU1ODY4LCJzdWIiOiJkNThhZGZkNzkzNzgzN2I1NTQxNzE5M2QyZTAzNzg2ZSJ9.zR-ldRiNsn-iqOQ-S1_XPrbazyX-OyppZGj_2G3whxc'
)
FLEXPAY_MERCHANT = os.environ.get('FLEXPAY_MERCHANT', 'JCONSULTMY')

# Logging configuration for email output and debugging
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
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'sisep.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'django.core.mail': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'core': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
