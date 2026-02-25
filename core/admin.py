from django.contrib import admin
from .models import ProfilUtilisateur

@admin.register(ProfilUtilisateur)
class ProfilUtilisateurAdmin(admin.ModelAdmin):
    list_display = ('user', 'institution', 'role', 'actif')
    list_filter = ('role', 'actif')
