from django.contrib import admin
from .models import (
    TerritoireVille,
    ProvAdmin,
    SecteurCommune,
    GroupementQuartier,
    VillageQuartier,
    TypeInstitution,
    Institution,
    EtatAgrement,
    EtatAdministrative,
    AdresseContact,
    Personne,
    Fonction,
    Membre,
    Mandat,
)


@admin.register(ProvAdmin)
class ProvAdminAdmin(admin.ModelAdmin):
    list_display = ('code', 'designation')
    search_fields = ('designation', 'code')


@admin.register(TerritoireVille)
class TerritoireVilleAdmin(admin.ModelAdmin):
    list_display = ('code', 'designation', 'province_admin')
    list_filter = ('province_admin',)
    search_fields = ('designation', 'code')


@admin.register(SecteurCommune)
class SecteurCommuneAdmin(admin.ModelAdmin):
    list_display = ('designation', 'territoire')
    list_filter = ('territoire',)


@admin.register(GroupementQuartier)
class GroupementQuartierAdmin(admin.ModelAdmin):
    list_display = ('designation', 'secteur')
    list_filter = ('secteur__territoire',)


@admin.register(VillageQuartier)
class VillageQuartierAdmin(admin.ModelAdmin):
    list_display = ('designation', 'groupement')
    list_filter = ('groupement__secteur__territoire',)


@admin.register(TypeInstitution)
class TypeInstitutionAdmin(admin.ModelAdmin):
    list_display = ('code', 'designation')


@admin.register(EtatAgrement)
class EtatAgrementAdmin(admin.ModelAdmin):
    list_display = ('code', 'designation')


@admin.register(EtatAdministrative)
class EtatAdministrativeAdmin(admin.ModelAdmin):
    list_display = ('num_agrement_admin', 'date_delivrance', 'etat_agrement', 'validation_admin', 'valid_tec_sportive')
    list_filter = ('etat_agrement',)


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom_officiel', 'sigle', 'type_institution', 'institution_tutelle')
    list_filter = ('type_institution',)
    search_fields = ('nom_officiel', 'sigle', 'code')
    raw_id_fields = ('institution_tutelle', 'etat_administrative', 'type_institution')


@admin.register(AdresseContact)
class AdresseContactAdmin(admin.ModelAdmin):
    list_display = ('avenue', 'numero', 'quartier_village', 'institution')
    list_filter = ('institution',)


@admin.register(Personne)
class PersonneAdmin(admin.ModelAdmin):
    list_display = ('nom', 'postnom', 'prenom', 'sexe', 'email')
    search_fields = ('nom', 'postnom', 'prenom')


@admin.register(Fonction)
class FonctionAdmin(admin.ModelAdmin):
    list_display = ('designation', 'ordre_priorite')


@admin.register(Membre)
class MembreAdmin(admin.ModelAdmin):
    list_display = ('personne', 'institution', 'fonction')
    list_filter = ('institution', 'fonction')


@admin.register(Mandat)
class MandatAdmin(admin.ModelAdmin):
    list_display = ('membre', 'date_debut', 'date_fin', 'statut_mandat')
    list_filter = ('membre__institution', 'membre__fonction', 'statut_mandat')
    raw_id_fields = ('membre',)
