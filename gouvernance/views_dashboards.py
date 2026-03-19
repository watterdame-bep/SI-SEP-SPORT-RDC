"""
Vues pour les dashboards du Ministre et SG.
"""
from datetime import date, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.messages import get_messages
from django.db.models import Count, Q
from django.utils import timezone

from core.permissions import require_role
from core.models import RoleUtilisateur
from gouvernance.models import Institution, Agent, Mandat, ProvAdmin, DisciplineSport, ValidationFederation, ValidationLigue, DivisionProvinciale


def _get_ministere_racine():
    """Retourne l'institution Ministère (racine)."""
    return Institution.objects.filter(institution_tutelle__isnull=True).first()


def _institutions_for_province(province_id):
    """Retourne les IDs d'institutions ayant au moins une adresse dans la province donnée."""
    if not province_id:
        return None
    return list(
        Institution.objects.filter(
            adresses_contact__groupement_quartier__secteur__territoire__province_admin_id=province_id
        ).values_list('uid', flat=True).distinct()
    )


@login_required
@require_role('MINISTRE')
def minister_dashboard(request):
    """
    Tableau de bord Ministre : vue d'ensemble avec statistiques.
    """
    # Ne pas afficher sur le dashboard les messages des autres interfaces
    list(get_messages(request))
    from datetime import datetime
    
    # Fédérations en attente de signature
    en_attente = Institution.objects.filter(
        statut_signature='ATTENTE_SIGNATURE',
        niveau_territorial='FEDERATION'
    ).select_related(
        'type_institution', 
        'institution_tutelle'
    ).prefetch_related(
        'disciplines'
    ).order_by('-date_demande_agrement', 'nom_officiel')
    
    # Statistiques globales
    total_federations = Institution.objects.filter(
        niveau_territorial='FEDERATION',
        statut_signature='SIGNE',
        statut_activation='ACTIVE'
    ).count()
    
    # Nombre de ligues provinciales
    total_ligues = Institution.objects.filter(
        niveau_territorial='LIGUE',
        statut_activation='ACTIVE'
    ).count()
    
    # Nombre de clubs
    total_clubs = Institution.objects.filter(
        niveau_territorial='CLUB',
        statut_activation='ACTIVE'
    ).count()
    
    # Nombre d'athlètes certifiés nationalement
    from gouvernance.models import Athlete
    total_athletes = Athlete.objects.filter(
        actif=True,
        statut_certification='CERTIFIE_NATIONAL'
    ).count()
    
    # Nombre d'infrastructures
    from infrastructures.models import Infrastructure
    total_infrastructures = Infrastructure.objects.filter(statut='VALIDEE').count()
    
    # Recette totale des infrastructures pour cette année
    from infrastructures.models import Vente
    from django.db.models import Sum, Q
    from datetime import datetime
    import json
    
    annee_courante = datetime.now().year
    
    # Filtrer les ventes de l'année avec statut VALIDE dans les notes
    ventes_annee = Vente.objects.filter(date_vente__year=annee_courante)
    
    # Calculer la recette totale en vérifiant le statut dans les notes
    recette_totale_annee = 0
    for vente in ventes_annee:
        try:
            if vente.notes:
                notes_data = json.loads(vente.notes)
                statut = notes_data.get('statut_paiement', 'INITIE')
                if statut == 'VALIDE':
                    recette_totale_annee += float(vente.montant_total)
        except (json.JSONDecodeError, TypeError):
            # Si les notes ne sont pas valides, on considère la vente comme valide
            recette_totale_annee += float(vente.montant_total)
    
    # Nombre de disciplines sportives
    disciplines_count = DisciplineSport.objects.filter(actif=True).count()
    
    # Taux de validation ce mois
    debut_mois = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    validees_ce_mois = Institution.objects.filter(
        niveau_territorial='FEDERATION',
        statut_signature='SIGNE',
        date_demande_agrement__gte=debut_mois
    ).count()
    
    demandes_ce_mois = Institution.objects.filter(
        niveau_territorial='FEDERATION',
        date_demande_agrement__gte=debut_mois
    ).count()
    
    taux_validation = round((validees_ce_mois / demandes_ce_mois * 100), 1) if demandes_ce_mois > 0 else 0
    
    # Historique récent (10 dernières actions)
    historique = Institution.objects.filter(
        niveau_territorial='FEDERATION',
        statut_signature__in=['SIGNE', 'REFUSE']
    ).select_related('type_institution').order_by('-date_demande_agrement')[:10]
    
    stats = {
        'en_attente': en_attente.count(),
        'total_federations': total_federations,
        'total_ligues': total_ligues,
        'total_clubs': total_clubs,
        'total_athletes': total_athletes,
        'total_infrastructures': total_infrastructures,
        'disciplines': disciplines_count,
        'taux_validation': taux_validation,
        'recette_totale_annee': recette_totale_annee,
        'annee_courante': annee_courante,
    }

    return render(request, 'gouvernance/minister_dashboard.html', {
        'en_attente': en_attente,
        'historique': historique,
        'stats': stats,
        'user_role': 'ministre',
        'now': timezone.now(),
        'nb_courriers_attente': en_attente.count(),
    })


@login_required
@require_role('INSTITUTION_ADMIN')
def sg_dashboard(request):
    """
    Dashboard du Secrétaire Général : widgets de performance, parapheur technique,
    filtre territorial (Province), quick-action par code d'homologation.
    """
    # Ne pas afficher sur le dashboard les messages des autres interfaces
    list(get_messages(request))
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    ministere = _get_ministere_racine()
    if not ministere:
        messages.error(request, "Aucun ministère trouvé. Effectuez d'abord l'initialisation du système.")
        return redirect('core:home')

    province_id = request.GET.get('province', '').strip() or None
    quick_q = request.GET.get('q', '').strip()

    # Filtre territorial : IDs d'institutions de la province (ou None = toutes)
    inst_ids_province = _institutions_for_province(province_id) if province_id else None

    base_fed = Institution.objects.filter(
        institution_tutelle=ministere,
        type_institution__code='FEDERATION',
    )
    if inst_ids_province is not None:
        base_fed = base_fed.filter(uid__in=inst_ids_province)

    # Card 1 : Fédérations actives (signées par le Ministre)
    # Les fédérations sont nationales, donc pas de filtre provincial ni de tutelle
    fed_actives = Institution.objects.filter(
        niveau_territorial='FEDERATION',
        type_institution__code='FEDERATION',
        statut_signature='SIGNE',
        statut_activation='ACTIVE'
    ).count()

    # Card 2 : Ligues provinciales
    base_ligues = Institution.objects.filter(niveau_territorial='LIGUE')
    if inst_ids_province is not None:
        base_ligues = base_ligues.filter(uid__in=inst_ids_province)
    ligues_count = base_ligues.filter(statut_activation='ACTIVE').count()

    # Card 3 : Clubs
    base_clubs = Institution.objects.filter(niveau_territorial='CLUB')
    if inst_ids_province is not None:
        base_clubs = base_clubs.filter(uid__in=inst_ids_province)
    clubs_count = base_clubs.filter(statut_activation='ACTIVE').count()

    # Card 4 : Athlètes certifiés nationalement
    from gouvernance.models import Athlete
    athletes_count = Athlete.objects.filter(
        actif=True,
        statut_certification='CERTIFIE_NATIONAL'
    ).count()

    # Card 5 : Infrastructures
    from infrastructures.models import Infrastructure
    infrastructures_count = Infrastructure.objects.filter(statut='VALIDEE').count()

    # Card 6 : Dossiers en attente (demandes d'agrément avec statut EN_INSTRUCTION)
    base_inst = Institution.objects.all()
    if inst_ids_province is not None:
        base_inst = base_inst.filter(uid__in=inst_ids_province)
    dossiers_attente = base_inst.filter(
        etat_administrative__etat_agrement__code='EN_INSTRUCTION'
    ).count()

    # Card 7 : Alertes de conformité (mandats qui expirent dans < 3 mois)
    in_3_months = date.today() + timedelta(days=90)
    alertes_mandats = Mandat.objects.filter(
        date_fin__isnull=False,
        date_fin__gte=date.today(),
        date_fin__lte=in_3_months,
        statut_mandat__icontains='cours',
    ).count()

    # Card 8 : Utilisateurs connectés (personnels administratifs actifs)
    users_actifs = User.objects.filter(is_active=True).count()

    # Parapheur : 10 dernières "demandes" (institutions avec agrément, ordre par date)
    parapheur_qs = Institution.objects.filter(
        etat_administrative__isnull=False
    ).select_related(
        'type_institution',
        'etat_administrative',
        'etat_administrative__etat_agrement',
    ).order_by('-etat_administrative__date_delivrance', '-etat_administrative__uid')[:10]
    if inst_ids_province is not None:
        parapheur_qs = parapheur_qs.filter(uid__in=inst_ids_province)
    parapheur = list(parapheur_qs)
    
    # Fédérations en attente d'inspection provinciale
    federations_en_inspection = Institution.objects.filter(
        niveau_territorial='FEDERATION',
        statut_inspection='EN_INSPECTION'
    ).select_related('type_institution').order_by('-date_demande_agrement')
    if inst_ids_province is not None:
        federations_en_inspection = federations_en_inspection.filter(uid__in=inst_ids_province)
    
    # Fédérations en attente de signature du Ministre (inspection validée)
    federations_attente_signature = Institution.objects.filter(
        niveau_territorial='FEDERATION',
        statut_signature='ATTENTE_SIGNATURE',
        statut_inspection='INSPECTION_VALIDEE'
    ).select_related('type_institution').order_by('-date_demande_agrement')
    if inst_ids_province is not None:
        federations_attente_signature = federations_attente_signature.filter(uid__in=inst_ids_province)
    
    # Fédérations refusées par le Ministre
    federations_refusees = Institution.objects.filter(
        niveau_territorial='FEDERATION',
        statut_signature='REFUSE'
    ).select_related('type_institution').order_by('-date_demande_agrement')
    if inst_ids_province is not None:
        federations_refusees = federations_refusees.filter(uid__in=inst_ids_province)

    # Validations d'inspection complétées par la direction provinciale — à vérifier / transférer au Ministre
    # (fédération encore en EN_INSPECTION tant que le SG n'a pas cliqué sur Transférer)
    validations_completes = ValidationFederation.objects.filter(
        statut__in=['VALIDEE', 'REJETEE'],
        federation__statut_inspection='EN_INSPECTION',
        federation__niveau_territorial='FEDERATION',
    ).select_related('federation', 'province', 'chef_division__personne').order_by('-date_validation')
    if inst_ids_province is not None:
        validations_completes = validations_completes.filter(federation_id__in=inst_ids_province)

    # Quick-action : recherche par code d'homologation (ex: RDC-FED-001)
    if quick_q:
        match = Institution.objects.filter(code__icontains=quick_q).first()
        if match:
            messages.info(request, f"Fédération trouvée : {match.nom_officiel} ({match.code}).")
        else:
            messages.warning(request, f"Aucune institution avec le code « {quick_q} ».")

    provinces = ProvAdmin.objects.all().order_by('designation')

    return render(request, 'gouvernance/sg_dashboard.html', {
        'ministere': ministere,
        'fed_actives': fed_actives,
        'ligues_count': ligues_count,
        'clubs_count': clubs_count,
        'athletes_count': athletes_count,
        'infrastructures_count': infrastructures_count,
        'dossiers_attente': dossiers_attente,
        'alertes_mandats': alertes_mandats,
        'users_actifs': users_actifs,
        'parapheur': parapheur,
        'federations_en_inspection': federations_en_inspection,
        'federations_attente_signature': federations_attente_signature,
        'federations_refusees': federations_refusees,
        'validations_completes': validations_completes,
        'provinces': provinces,
        'province_id': province_id or '',
        'quick_q': quick_q,
        'user_role': 'sg',
    })


@login_required
@require_role('DIRECTEUR_PROVINCIAL')
def directeur_provincial_dashboard(request):
    """
    Dashboard du Directeur Provincial : poste de contrôle local pour sa province.
    Affiche les enquêtes de viabilité, clubs/ligues, infrastructures et rapports.
    """
    # Ne pas afficher sur le dashboard les messages des autres interfaces
    list(get_messages(request))
    from gouvernance.models import DivisionProvinciale, ValidationFederation
    
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    # Récupérer la province du Directeur Provincial
    province = profil.province_admin
    if not province:
        messages.error(request, "Aucune province associée à votre profil.")
        return redirect('core:home')
    
    # Récupérer la division provinciale
    try:
        division = DivisionProvinciale.objects.get(province=province)
    except DivisionProvinciale.DoesNotExist:
        messages.error(request, "Division provinciale non trouvée.")
        return redirect('core:home')
    
    # Fédérations implantées dans cette province
    # Chercher par provinces_implantation OU par adresses dans la province
    federations_province = Institution.objects.filter(
        niveau_territorial='FEDERATION'
    ).filter(
        Q(provinces_implantation=province) |
        Q(adresses_contact__groupement_quartier__secteur__territoire__province_admin=province)
    ).select_related('type_institution').distinct().order_by('nom_officiel')
    
    # Récupérer les validations de fédérations pour cette province
    validations = ValidationFederation.objects.filter(
        province=province
    ).select_related(
        'federation',
        'chef_division__personne'
    ).order_by('-date_creation')
    
    # Statistiques KPI
    validations_en_attente = validations.filter(statut='EN_ATTENTE')
    validations_acceptees = validations.filter(statut='VALIDEE')
    validations_rejetees = validations.filter(statut='REJETEE')
    
    stats = {
        'enquetes_en_attente': validations_en_attente.count(),
        'ligues_recensees': federations_province.count(),
        'infrastructures': 0,  # À implémenter avec le modèle Infrastructure
        'validations_acceptees': validations_acceptees.count(),
        'validations_rejetees': validations_rejetees.count(),
    }
    
    return render(request, 'gouvernance/directeur_provincial_dashboard.html', {
        'province': province,
        'division': division,
        'validations': validations,
        'validations_en_attente': validations_en_attente.select_related('federation').order_by('-date_creation'),
        'federations_province': federations_province,
        'stats': stats,
        'user_role': 'directeur_provincial',
    })


@login_required
@require_role('DIRECTEUR_PROVINCIAL')
def enquetes_viabilite(request):
    """
    Interface dédiée aux enquêtes de viabilité pour le Directeur Provincial.
    Affiche les validations de fédérations ET les ligues à inspecter.
    """
    from gouvernance.models import DivisionProvinciale, ValidationFederation, ValidationLigue
    
    try:
        profil = request.user.profil_sisep
    except:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('core:home')
    
    # Récupérer la province du Directeur Provincial
    province = profil.province_admin
    if not province:
        messages.error(request, "Aucune province associée à votre profil.")
        return redirect('core:home')
    
    # Récupérer la division provinciale
    try:
        division = DivisionProvinciale.objects.get(province=province)
    except DivisionProvinciale.DoesNotExist:
        messages.error(request, "Division provinciale non trouvée.")
        return redirect('core:home')
    
    # Récupérer les validations de fédérations pour cette province
    validations = ValidationFederation.objects.filter(
        province=province
    ).select_related(
        'federation',
        'chef_division__personne'
    ).order_by('-date_creation')
    
    # Récupérer les ligues à valider pour cette division (toutes les validations)
    validations_ligues = ValidationLigue.objects.filter(
        division_provinciale=division
    ).select_related(
        'ligue',
        'ligue__institution_tutelle',
        'ligue__province_admin'
    ).order_by('-date_creation')
    
    # Statistiques KPI - Fédérations
    validations_en_attente = validations.filter(statut='EN_ATTENTE')
    validations_acceptees = validations.filter(statut='VALIDEE')
    validations_rejetees = validations.filter(statut='REJETEE')
    
    # Statistiques KPI - Ligues
    ligues_en_inspection = validations_ligues.filter(statut='EN_INSPECTION')
    ligues_validees = validations_ligues.filter(statut='INSPECTION_VALIDEE')
    ligues_rejetees = validations_ligues.filter(statut='INSPECTION_REJETEE')
    
    stats = {
        'enquetes_en_attente': validations_en_attente.count(),
        'validations_acceptees': validations_acceptees.count(),
        'validations_rejetees': validations_rejetees.count(),
        'ligues_en_inspection': ligues_en_inspection.count(),
        'ligues_validees': ligues_validees.count(),
        'ligues_rejetees': ligues_rejetees.count(),
    }
    
    return render(request, 'gouvernance/enquetes_viabilite.html', {
        'province': province,
        'division': division,
        'validations': validations,
        'validations_en_attente': validations_en_attente.select_related('federation').order_by('-date_creation'),
        'validations_ligues': validations_ligues,
        'ligues_en_inspection': ligues_en_inspection,
        'stats': stats,
        'user_role': 'directeur_provincial',
    })


@login_required
@require_role('INSTITUTION_ADMIN')
def inspections_a_transferer(request):
    """
    Interface dédiée pour transférer les inspections complétées au Ministre.
    Accessible depuis l'interface des fédérations nationales du SG.
    """
    from gouvernance.models import ValidationFederation
    
    ministere = _get_ministere_racine()
    if not ministere:
        messages.error(request, "Aucun ministère trouvé.")
        return redirect('core:home')

    province_id = request.GET.get('province', '').strip() or None
    inst_ids_province = _institutions_for_province(province_id) if province_id else None

    # Récupérer les validations complétées (validées ou rejetées)
    validations_completes = ValidationFederation.objects.filter(
        statut__in=['VALIDEE', 'REJETEE']
    ).select_related('federation', 'province', 'chef_division__personne').order_by('-date_validation')
    
    if inst_ids_province is not None:
        validations_completes = validations_completes.filter(federation_id__in=inst_ids_province)

    # Statistiques
    validations_acceptees = validations_completes.filter(statut='VALIDEE').count()
    validations_rejetees = validations_completes.filter(statut='REJETEE').count()
    total_validations = validations_completes.count()
    # En attente = validées/rejetées mais pas encore transférées au Ministre
    validations_en_attente = validations_completes.filter(federation__statut_signature='').count()

    provinces = ProvAdmin.objects.all().order_by('designation')

    return render(request, 'gouvernance/inspections_a_transferer.html', {
        'validations_completes': validations_completes,
        'validations_acceptees': validations_acceptees,
        'validations_rejetees': validations_rejetees,
        'validations_en_attente': validations_en_attente,
        'total_validations': total_validations,
        'provinces': provinces,
        'province_id': province_id or '',
        'user_role': 'sg',
    })
