"""SI-SEP Sport RDC - URL Configuration."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('parametres/', include('parametres.urls')),
    path('parametres-geographiques/', include('referentiel_geo.urls')),
    path('gouvernance/', include('gouvernance.urls')),
    path('api/infrastructures/', include('infrastructures.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
