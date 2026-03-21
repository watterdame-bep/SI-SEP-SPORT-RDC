"""
Vues pour la gestion des Fédérations Nationales
Réservé au Secrétaire Général
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q, Count
from django.views.decorators.http import require_http_methods
from datetime import date, timedelta
import json

from gouvernance.models import Institution, TypeInstitution
from gouvernance.models.discipline import DisciplineSport
from gouvernance.models.agrement import EtatAdministrative
from core.permissions import est_secretaire_general_ministere, est_sg_ou_ministre, est_ministre


def _user_passes_test(test_func, login_url=None):
    from django.contrib.auth.views import redirect_to_login
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            return redirect_to_login(request.get_full_path(), login_url=login_url)
        return wrapper
    return decorator


@login_required(login_url='/auth/login/')
@_user_passes_test(est_sg_ou_ministre, login_url='/auth/login/')
def federations_nationales(request):
    """
    Page principale de gestion des Fédérations Nationales
    """
    # Récupérer toutes les fédérations
    federations = Institution.objects.filter(
        niveau_territorial='FEDERATION'
    ).select_related(
        'type_institution',
        'etat_administrative'
    ).prefetch_related(
        'institutions_fille',
        'disciplines',
        'adresses_contact__groupement_quartier__secteur__territoire__province_admin'
    ).annotate(
        nb_ligues=Count('institutions_fille', filter=Q(institutions_fille__niveau_territorial='LIGUE'))
    )
    
    # Statistiques globales
    total_federations = federations.count()
    
    # Fédérations en attente de signature du Ministre
    en_attente = federations.filter(statut_signature='ATTENTE_SIGNATURE').count()
    
    # Fédérations avec agrément expiré
    # TODO: Implémenter la logique d'expiration basée sur date_delivrance + durée validité
    agrement_expire = 0
    
    # Nombre de disciplines sportives couvertes par les fédérations
    disciplines_couvertes = DisciplineSport.objects.filter(
        federations__isnull=False
    ).distinct().count()
    
    # Fédérations refusées
    refusees = federations.filter(statut_signature='REFUSE').count()
    
    # Alertes: agréments qui expirent bientôt
    # TODO: Implémenter les alertes basées sur date_delivrance + durée validité
    alertes = []
    
    # Répartition géographique (basée sur niveau_territorial)
    # TODO: Ajouter un champ province dans Institution ou via AdresseContact
    repartition_geo = {}
    
    # Fédérations agréées (signées)
    agreees = federations.filter(statut_signature='SIGNE').count()

    stats = {
        'total': total_federations,
        'agreees': agreees,
        'en_attente': en_attente,
        'agrement_expire': agrement_expire,
        'refusees': refusees,
        'disciplines': disciplines_couvertes,
        'taux_conformite': round((total_federations - agrement_expire) / total_federations * 100, 1) if total_federations > 0 else 0,
    }
    
    # Récupérer toutes les disciplines pour le filtre
    disciplines = DisciplineSport.objects.all().order_by('designation')
    
    # Récupérer toutes les provinces pour le filtre
    from gouvernance.models.localisation import ProvAdmin
    provinces = ProvAdmin.objects.all().order_by('designation')
    
    is_ministre = est_ministre(request.user)

    # Le ministre ne voit que les fédérations officiellement agréées (signées)
    if is_ministre:
        federations = federations.filter(statut_signature='SIGNE')
        total = federations.count()
        stats = {
            'total': total,
            'agreees': total,
            'en_attente': 0,
            'agrement_expire': 0,
            'refusees': 0,
            'disciplines': disciplines_couvertes,
            'taux_conformite': 100 if total > 0 else 0,
        }

    context = {
        'federations': federations,
        'stats': stats,
        'alertes': alertes,
        'repartition_geo': repartition_geo,
        'disciplines': disciplines,
        'provinces': provinces,
        'user_role': 'ministre' if is_ministre else 'sg',
        'is_ministre': is_ministre,
    }
    
    return render(request, 'gouvernance/federations_nationales.html', context)


@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
def federation_create(request):
    """
    Formulaire de création d'une nouvelle fédération
    """
    from gouvernance.models import TypeInstitution, ProvAdmin
    from gouvernance.models.discipline import DisciplineSport
    from gouvernance.models.localisation import TerritoireVille, SecteurCommune, GroupementQuartier
    from datetime import datetime
    
    # Générer le code automatiquement
    # Format: FED-XXXX (XXXX = numéro séquentiel)
    derniere_federation = Institution.objects.filter(
        niveau_territorial='FEDERATION',
        code__startswith='FED-'
    ).order_by('-code').first()
    
    if derniere_federation and derniere_federation.code:
        try:
            dernier_numero = int(derniere_federation.code.split('-')[1])
            nouveau_numero = dernier_numero + 1
        except (IndexError, ValueError):
            nouveau_numero = 1
    else:
        nouveau_numero = 1
    
    code_genere = f"FED-{nouveau_numero:04d}"
    
    # Générer le numéro de dossier automatiquement
    # Format: DOSS-YYYY-XXXX (YYYY = année, XXXX = numéro séquentiel)
    annee_actuelle = datetime.now().year
    dernier_dossier = Institution.objects.filter(
        niveau_territorial='FEDERATION',
        numero_dossier__startswith=f'DOSS-{annee_actuelle}-'
    ).order_by('-numero_dossier').first()
    
    if dernier_dossier and dernier_dossier.numero_dossier:
        try:
            dernier_numero_dossier = int(dernier_dossier.numero_dossier.split('-')[2])
            nouveau_numero_dossier = dernier_numero_dossier + 1
        except (IndexError, ValueError):
            nouveau_numero_dossier = 1
    else:
        nouveau_numero_dossier = 1
    
    numero_dossier_genere = f"DOSS-{annee_actuelle}-{nouveau_numero_dossier:04d}"
    
    # Récupérer le type institution "Fédération"
    type_federation = TypeInstitution.objects.filter(code='FEDERATION').first()
    if not type_federation:
        # Créer le type si il n'existe pas
        type_federation = TypeInstitution.objects.create(
            code='FEDERATION',
            designation='Fédération Nationale'
        )
    
    # Récupérer les données pour les selects
    disciplines = DisciplineSport.objects.filter(actif=True).order_by('designation')
    provinces = ProvAdmin.objects.all().order_by('designation')
    
    context = {
        'type_federation': type_federation,
        'disciplines': disciplines,
        'provinces': provinces,
        'code_genere': code_genere,
        'numero_dossier_genere': numero_dossier_genere,
        'user_role': 'sg',
    }
    
    return render(request, 'gouvernance/federation_create.html', context)


@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
@require_http_methods(["POST"])
def federation_store(request):
    """
    Enregistrer une nouvelle fédération avec tous les champs et documents
    """
    try:
        from gouvernance.models.discipline import DisciplineSport
        from gouvernance.models.contact import AdresseContact
        from gouvernance.models.localisation import GroupementQuartier
        
        # Étape 1: Identité
        code = request.POST.get('code', '').strip().upper()
        nom_officiel = request.POST.get('nom_officiel', '').strip()
        sigle = request.POST.get('sigle', '').strip().upper()
        numero_dossier = request.POST.get('numero_dossier', '').strip()
        discipline_id = request.POST.get('disciplines')
        type_institution_id = request.POST.get('type_institution')
        statut_juridique = request.POST.get('statut_juridique', '').strip()
        date_creation = request.POST.get('date_creation') or None
        nombre_pers_admin = int(request.POST.get('nombre_pers_admin', 0) or 0)
        nombre_pers_tech = int(request.POST.get('nombre_pers_tech', 0) or 0)
        partenaire = request.POST.get('partenaire', '').strip()
        logo = request.FILES.get('logo')
        
        # Étape 2: Localisation
        avenue = request.POST.get('avenue', '').strip()
        numero = request.POST.get('numero') or None
        groupement_quartier_id = request.POST.get('groupement_quartier')
        telephone_off = request.POST.get('telephone_off', '').strip()
        email_officiel = request.POST.get('email_officiel', '').strip()
        site_web = request.POST.get('site_web', '').strip()
        
        # Étape 3: Agrément
        type_agrement_sollicite = request.POST.get('type_agrement_sollicite', '').strip()
        date_demande_agrement = request.POST.get('date_demande_agrement') or None
        duree_sollicitee = request.POST.get('duree_sollicitee', '4')
        
        # Provinces d'implantation
        provinces_implantation_ids = request.POST.getlist('provinces_implantation')
        
        # Étape 4: Responsables
        nom_president = request.POST.get('nom_president', '').strip()
        telephone_president = request.POST.get('telephone_president', '').strip()
        
        # Étape 5: Documents
        document_statuts = request.FILES.get('document_statuts')
        document_pv_ag = request.FILES.get('document_pv_ag')
        document_liste_membres = request.FILES.get('document_liste_membres')
        document_certificat = request.FILES.get('document_certificat')
        
        # Validation des champs obligatoires
        if not code or not nom_officiel or not sigle:
            return JsonResponse({
                'success': False,
                'message': 'Le code, le nom officiel et le sigle sont obligatoires'
            }, status=400)
        
        if not discipline_id:
            return JsonResponse({
                'success': False,
                'message': 'Veuillez sélectionner une discipline sportive'
            }, status=400)
        
        if not type_institution_id:
            return JsonResponse({
                'success': False,
                'message': 'Veuillez sélectionner un type d\'institution'
            }, status=400)
        
        if not telephone_off or not email_officiel:
            return JsonResponse({
                'success': False,
                'message': 'Le téléphone et l\'email sont obligatoires'
            }, status=400)
        
        if not type_agrement_sollicite or not date_demande_agrement:
            return JsonResponse({
                'success': False,
                'message': 'Les informations sur l\'agrément sont obligatoires'
            }, status=400)
        
        if not nom_president or not telephone_president:
            return JsonResponse({
                'success': False,
                'message': 'Les informations du président sont obligatoires'
            }, status=400)
        
        if not document_statuts or not document_pv_ag or not document_liste_membres:
            return JsonResponse({
                'success': False,
                'message': 'Les documents obligatoires (Statuts, PV AG, Liste membres) doivent être fournis'
            }, status=400)
        
        # Vérifier que minimum 6 provinces sont sélectionnées
        if len(provinces_implantation_ids) < 6:
            return JsonResponse({
                'success': False,
                'message': 'Veuillez sélectionner au moins 6 provinces d\'implantation'
            }, status=400)
        
        # Vérifier si le code existe déjà
        if Institution.objects.filter(code=code).exists():
            return JsonResponse({
                'success': False,
                'message': f'Une institution avec le code "{code}" existe déjà'
            }, status=400)
        
        # Créer l'institution avec tous les champs
        institution = Institution.objects.create(
            code=code,
            nom_officiel=nom_officiel,
            sigle=sigle,
            numero_dossier=numero_dossier,
            type_institution_id=type_institution_id,
            statut_juridique=statut_juridique,
            date_creation=date_creation,
            nombre_pers_admin=nombre_pers_admin,
            nombre_pers_tech=nombre_pers_tech,
            partenaire=partenaire,
            logo=logo if logo else None,
            email_officiel=email_officiel,
            telephone_off=telephone_off,
            site_web=site_web,
            niveau_territorial='FEDERATION',
            statut_activation='ACTIVE',
            statut_inspection='AUDIT',  # En attente d'audit provincial
            statut_signature='',  # Pas encore en attente de signature
            # Agrément
            type_agrement_sollicite=type_agrement_sollicite,
            date_demande_agrement=date_demande_agrement,
            duree_sollicitee=int(duree_sollicitee) if duree_sollicitee else 4,
            # Responsables
            nom_president=nom_president,
            telephone_president=telephone_president,
            # Documents
            document_statuts=document_statuts,
            document_pv_ag=document_pv_ag,
            document_liste_membres=document_liste_membres,
            document_certificat=document_certificat if document_certificat else None,
        )
        
        # Ajouter la discipline
        if discipline_id:
            institution.disciplines.add(discipline_id)
        
        # Ajouter les provinces d'implantation
        if provinces_implantation_ids:
            institution.provinces_implantation.set(provinces_implantation_ids)
        
        # Créer l'adresse si fournie
        if groupement_quartier_id:
            AdresseContact.objects.create(
                avenue=avenue,
                numero=numero,
                groupement_quartier_id=groupement_quartier_id,
                institution=institution
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Fédération "{nom_officiel}" créée avec succès. Le dossier a été transmis aux Directeurs Provinciaux pour inspection de viabilité.',
            'redirect_url': '/gouvernance/federations/'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de l\'enregistrement: {str(e)}'
        }, status=500)


@login_required(login_url='/auth/login/')
@_user_passes_test(est_sg_ou_ministre, login_url='/auth/login/')
def federation_detail(request, pk):
    """
    Détails d'une fédération — accessible SG et Ministre
    """
    federation = get_object_or_404(
        Institution.objects.select_related(
            'type_institution',
            'etat_administrative'
        ).prefetch_related(
            'institutions_fille',
            'disciplines'
        ),
        pk=pk,
        niveau_territorial='FEDERATION'
    )

    ligues = federation.institutions_fille.filter(niveau_territorial='LIGUE')
    is_ministre = est_ministre(request.user)

    context = {
        'federation': federation,
        'ligues': ligues,
        'user_role': 'ministre' if is_ministre else 'sg',
        'is_ministre': is_ministre,
    }

    return render(request, 'gouvernance/federation_detail.html', context)


@login_required(login_url='/login/')
@require_http_methods(["GET"])
def federation_download_arrete(request, pk):
    """
    Télécharger l'Arrêté Ministériel d'une fédération
    """
    from django.http import FileResponse, Http404
    
    federation = get_object_or_404(
        Institution,
        pk=pk,
        niveau_territorial='FEDERATION'
    )
    
    # Vérifier que l'arrêté existe
    if not federation.document_arrete:
        return JsonResponse({
            'success': False,
            'message': 'Aucun arrêté disponible pour cette fédération'
        }, status=404)
    
    # Marquer l'arrêté comme vu par le SG (si c'est le SG qui télécharge)
    try:
        profil = request.user.profil_sisep
        from core.models import RoleUtilisateur
        if profil.role == RoleUtilisateur.INSTITUTION_ADMIN and not federation.arrete_vu_par_sg:
            federation.arrete_vu_par_sg = True
            federation.save(update_fields=['arrete_vu_par_sg'])
    except:
        pass  # Si pas de profil, on continue quand même
    
    # Retourner le fichier PDF
    try:
        return FileResponse(
            federation.document_arrete.open('rb'),
            content_type='application/pdf',
            as_attachment=True,
            filename=f"Arrete_{federation.code}_{federation.numero_arrete.replace('/', '_')}.pdf"
        )
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors du téléchargement: {str(e)}'
        }, status=500)


@login_required(login_url='/login/')
@require_http_methods(["GET"])
def federation_download_certificat(request, pk):
    """
    Télécharger le Certificat d'Homologation d'une fédération
    """
    from django.http import FileResponse, Http404
    
    federation = get_object_or_404(
        Institution,
        pk=pk,
        niveau_territorial='FEDERATION'
    )
    
    # Vérifier que le certificat existe
    if not federation.document_certificat_homologation:
        return JsonResponse({
            'success': False,
            'message': 'Aucun certificat disponible pour cette fédération'
        }, status=404)
    
    # Retourner le fichier PDF
    try:
        return FileResponse(
            federation.document_certificat_homologation.open('rb'),
            content_type='application/pdf',
            as_attachment=True,
            filename=f"Certificat_{federation.code}_{federation.numero_homologation.replace('/', '_')}.pdf"
        )
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors du téléchargement: {str(e)}'
        }, status=500)


@login_required(login_url='/login/')
@_user_passes_test(est_secretaire_general_ministere, login_url='/login/')
@require_http_methods(["POST"])
def federation_delete(request, pk):
    """
    Supprimer une fédération (JSON API)
    """
    try:
        federation = get_object_or_404(
            Institution,
            pk=pk,
            niveau_territorial='FEDERATION'
        )
        
        nom_federation = federation.nom_officiel
        
        # Supprimer la fédération
        federation.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'La fédération "{nom_federation}" a été supprimée avec succès.'
        })
        
    except Institution.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Fédération non trouvée'
        }, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de la suppression: {str(e)}'
        }, status=500)
