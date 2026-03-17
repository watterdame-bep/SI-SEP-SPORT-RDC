"""SI-SEP Sport RDC - URL Configuration."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('public.urls')),  # Page d'accueil publique
    path('auth/', include('core.urls')),  # Authentification et dashboards
    path('verify-email/<str:token>/', core_views.verify_email, name='verify_email_direct'),  # Vérification email directe
    path('parametres/', include('parametres.urls')),
    path('parametres-geographiques/', include('referentiel_geo.urls')),
    path('gouvernance/', include('gouvernance.urls')),
    path('api/infrastructures/', include('infrastructures.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
