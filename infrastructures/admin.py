from django.contrib import admin
from .models import (
    TypeInfrastructure, Infrastructure, SuiviTechnique, RevenuInfrastructure,
    Evenement, ZoneStade, EvenementZone, Ticket, Vente,
)


@admin.register(TypeInfrastructure)
class TypeInfrastructureAdmin(admin.ModelAdmin):
    list_display = ('code', 'designation')


@admin.register(Infrastructure)
class InfrastructureAdmin(admin.ModelAdmin):
    list_display = ('code_homologation', 'nom', 'type_infrastructure', 'territoire', 'actif')
    list_filter = ('type_infrastructure', 'actif')
    search_fields = ('nom', 'code_homologation')
    raw_id_fields = ('territoire',)


@admin.register(SuiviTechnique)
class SuiviTechniqueAdmin(admin.ModelAdmin):
    list_display = ('infrastructure', 'date_controle', 'etat_general', 'capacite_spectateurs')
    list_filter = ('etat_general',)


@admin.register(RevenuInfrastructure)
class RevenuInfrastructureAdmin(admin.ModelAdmin):
    list_display = ('infrastructure', 'date_debut', 'type_revenu', 'montant', 'devise')
    list_filter = ('type_revenu', 'devise')


# ---------- Billetterie ----------

@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = ('titre', 'infrastructure', 'organisateur', 'type_evenement', 'date_evenement', 'heure_debut', 'actif')
    list_filter = ('type_evenement', 'actif', 'infrastructure')
    search_fields = ('titre',)
    raw_id_fields = ('infrastructure', 'organisateur')
    date_hierarchy = 'date_evenement'


@admin.register(ZoneStade)
class ZoneStadeAdmin(admin.ModelAdmin):
    list_display = ('nom', 'infrastructure', 'ordre')
    list_filter = ('infrastructure',)
    ordering = ('infrastructure', 'ordre', 'nom')


class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 0
    readonly_fields = ('uid', 'statut', 'date_creation')
    can_delete = True
    max_num = 50
    show_change_link = True


@admin.register(EvenementZone)
class EvenementZoneAdmin(admin.ModelAdmin):
    list_display = ('evenement', 'zone_stade', 'prix_unitaire', 'devise', 'capacite_max')
    list_filter = ('evenement__infrastructure',)
    raw_id_fields = ('evenement', 'zone_stade')


@admin.register(Vente)
class VenteAdmin(admin.ModelAdmin):
    list_display = ('date_vente', 'evenement', 'montant_total', 'devise', 'canal', 'reference_paiement')
    list_filter = ('canal', 'evenement')
    date_hierarchy = 'date_vente'
    readonly_fields = ('date_vente',)
    inlines = (TicketInline,)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('uid', 'evenement_zone', 'statut', 'vente', 'date_utilisation', 'date_creation')
    list_filter = ('statut', 'evenement_zone__evenement')
    search_fields = ('uid',)
    readonly_fields = ('uid', 'date_creation', 'date_utilisation')
    raw_id_fields = ('evenement_zone', 'vente')
