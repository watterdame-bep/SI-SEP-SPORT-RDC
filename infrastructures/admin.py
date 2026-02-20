from django.contrib import admin
from .models import TypeInfrastructure, Infrastructure, SuiviTechnique, RevenuInfrastructure


@admin.register(TypeInfrastructure)
class TypeInfrastructureAdmin(admin.ModelAdmin):
    list_display = ('code', 'designation')


@admin.register(Infrastructure)
class InfrastructureAdmin(admin.ModelAdmin):
    list_display = ('code_homologation', 'nom', 'type_infrastructure', 'territoire', 'actif')
    list_filter = ('type_infrastructure', 'actif')
    search_fields = ('nom', 'code_homologation')
    raw_id_fields = ('territoire', 'gestionnaire')


@admin.register(SuiviTechnique)
class SuiviTechniqueAdmin(admin.ModelAdmin):
    list_display = ('infrastructure', 'date_controle', 'etat_general', 'capacite_spectateurs')
    list_filter = ('etat_general',)


@admin.register(RevenuInfrastructure)
class RevenuInfrastructureAdmin(admin.ModelAdmin):
    list_display = ('infrastructure', 'date_debut', 'type_revenu', 'montant', 'devise')
    list_filter = ('type_revenu', 'devise')
