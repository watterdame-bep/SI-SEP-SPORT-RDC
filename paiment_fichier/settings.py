

from pathlib import Path
from datetime import timedelta
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: Keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-hf-2bauscp4!orn*@@v20p97)k%rfgeasabldf+ywilydmh$^j'

DEBUG = False

ALLOWED_HOSTS = ["*"]

# User Model Configuration
AUTH_USER_MODEL = 'auth.User'

APPEND_SLASH = True

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party packages
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',  # Cross-Origin Resource Sharing support

    # Custom applications
    'geographie',
    'utilisateurs',
    'comptes',
    'facturation',
    'paiements',
    'support',
    'notifications',
    'reminders',  # Application pour les reminders de paiement
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Middleware multilingue pour détecter et ajouter la langue
    'shared.language_middleware.LanguageMiddleware',
]


ROOT_URLCONF = 'snel.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'snel.wsgi.application'

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.environ.get('DB_NAME', 'snel_db'),
        'USER': os.environ.get('DB_USER', 'db'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'HelloT@lk17'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '600')),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Kinshasa'  # Congo-Kinshasa timezone (UTC+1)

USE_I18N = True
USE_TZ = True  # Utilise les timezones aware (important pour Kinshasa)

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # For production deployment
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Django REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',  # Require authentication by default
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 10  # Default number of items per page
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(weeks=1),  # Access token valid for 1 hour
    'REFRESH_TOKEN_LIFETIME': timedelta(weeks=1),   # Refresh token valid for 1 day
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# CORS Configuration - Security fix
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",   # Next.js dev server
    "http://localhost:3001",   # Next.js dev server (alternate port)
    "http://127.0.0.1:3000",   # Next.js dev server
    "http://127.0.0.1:3001",   # Next.js dev server
    "http://localhost:8080",   # Default for Flutter Web/Desktop
    "http://10.0.2.2:8080",    # Android emulator, if backend is on localhost
    "http://127.0.0.1:8000",   # For the API itself
    "http://localhost:8000",
    "https://snel-admin.devjconsultmy.com",  # Production frontend
]

# Development only - Disable in production for security
CORS_ALLOW_ALL_ORIGINS = DEBUG

# Allow credentials (cookies, auth headers) in CORS requests
CORS_ALLOW_CREDENTIALS = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Site configuration for payment readings
SITE_URL = 'https://snel-back.devjconsultmy.com'  

# Email configuration for SMTP (Gmail)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'dev.jconsult@gmail.com'
EMAIL_HOST_PASSWORD = 'ndlfauwjttiabfim'
DEFAULT_FROM_EMAIL = 'SNEL <dev.jconsult@gmail.com>'
# Firebase Cloud Functions configuration for notifications
FIREBASE_CLOUD_FUNCTIONS_BASE_URL = 'https://us-central1-my-snel-52c80.cloudfunctions.net'
FIREBASE_CLOUD_FUNCTIONS_URLS = {
    'send_notification': f'{FIREBASE_CLOUD_FUNCTIONS_BASE_URL}/sendNotification',
    'send_facture_notification': f'{FIREBASE_CLOUD_FUNCTIONS_BASE_URL}/sendFactureNotification',
    'send_releve_notification': f'{FIREBASE_CLOUD_FUNCTIONS_BASE_URL}/sendReleveNotification',
}

# Firebase credentials for Cloud Functions authentication
FIREBASE_SERVICE_ACCOUNT_KEY_PATH = os.path.join(BASE_DIR, 'my-snel-52c80-firebase-adminsdk-fbsvc-6166bdd510.json')

# Timeout for Cloud Functions calls (in seconds)
FIREBASE_FUNCTIONS_TIMEOUT = 30
SERVER_EMAIL = 'noreply@snel.com'

# FlexPay API configuration
FLEXPAY_API_URL = os.environ.get('FLEXPAY_API_URL', 'https://backend.flexpay.cd/api/rest/v1/paymentService')
FLEXPAY_CHECK_URL = os.environ.get('FLEXPAY_CHECK_URL', 'https://backend.flexpay.cd/api/rest/v1/check/')
FLEXPAY_BEARER_TOKEN = os.environ.get('FLEXPAY_BEARER_TOKEN', 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJcL2xvZ2luIiwicm9sZXMiOlsiTUVSQ0hBTlQiXSwiZXhwIjoxODI4NDU1ODY4LCJzdWIiOiJkNThhZGZkNzkzNzgzN2I1NTQxNzE5M2QyZTAzNzg2ZSJ9.zR-ldRiNsn-iqOQ-S1_XPrbazyX-OyppZGj_2G3whxc')