from django.contrib import admin
from .models import (
    TerritoireVille,
    ProvAdmin,
    SecteurCommune,
    GroupementQuartier,
    TypeInstitution,
    Institution,
    EtatAgrement,
    EtatAdministrative,
    AdresseContact,
    Personne,
    Fonction,
    Membre,
    Mandat,
    DisciplineSport,
    TypeCompetition,
    Competition,
    Journee,
    Rencontre,
    CalendrierCompetition,
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
    list_display = ('code', 'nom_officiel', 'sigle', 'type_institution', 'niveau_territorial', 'institution_tutelle')
    list_filter = ('type_institution', 'niveau_territorial')
    search_fields = ('nom_officiel', 'sigle', 'code')
    raw_id_fields = ('institution_tutelle', 'etat_administrative', 'type_institution')
    filter_horizontal = ('disciplines',)  # Interface pour gérer les ManyToMany


@admin.register(AdresseContact)
class AdresseContactAdmin(admin.ModelAdmin):
    list_display = ('avenue', 'numero', 'groupement_quartier', 'institution')
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


@admin.register(DisciplineSport)
class DisciplineSportAdmin(admin.ModelAdmin):
    list_display = ('code', 'designation', 'ordre', 'actif')
    list_filter = ('actif',)
    search_fields = ('code', 'designation')
    ordering = ('ordre', 'designation')


@admin.register(TypeCompetition)
class TypeCompetitionAdmin(admin.ModelAdmin):
    list_display = ('designation', 'code', 'ligue', 'ordre', 'actif')
    list_filter = ('ligue', 'actif')
    search_fields = ('designation', 'code')
    raw_id_fields = ('ligue',)


class CalendrierCompetitionInline(admin.TabularInline):
    model = CalendrierCompetition
    extra = 0
    raw_id_fields = ('infrastructure',)


try:
    admin.site.unregister(Competition)
except Exception:
    pass


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type_competition', 'organisateur', 'saison', 'categorie', 'actif')
    list_filter = ('organisateur', 'saison', 'categorie', 'actif')
    search_fields = ('titre', 'saison')
    raw_id_fields = ('type_competition', 'organisateur')
    inlines = [CalendrierCompetitionInline]


class RencontreInline(admin.TabularInline):
    model = Rencontre
    extra = 0
    raw_id_fields = ('equipe_a', 'equipe_b', 'stade', 'evenement')


@admin.register(Journee)
class JourneeAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'competition', 'ordre')
    list_filter = ('competition',)
    ordering = ('competition', 'ordre')
    raw_id_fields = ('competition',)
    inlines = [RencontreInline]


@admin.register(Rencontre)
class RencontreAdmin(admin.ModelAdmin):
    list_display = ('equipe_a', 'equipe_b', 'stade', 'date_heure', 'statut', 'evenement')
    list_filter = ('statut', 'journee__competition')
    date_hierarchy = 'date_heure'
    raw_id_fields = ('journee', 'equipe_a', 'equipe_b', 'stade', 'evenement')
