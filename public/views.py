# -*- coding: utf-8 -*-
"""
Vues publiques pour l'achat de billets sans connexion.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.db.models import Min
from django.contrib import messages

from gouvernance.models import Rencontre
from infrastructures.models import Evenement, EvenementZone


def home(request):
    """
    Page d'accueil publique du portail SI-SEP Sport RDC.
    """
    # Récupérer les prochaines rencontres avec billetterie configurée
    rencontres_a_venir = Rencontre.objects.filter(
        date_heure__gte=timezone.now(),
        evenement__isnull=False
    ).select_related(
        'journee__competition',
        'equipe_a',
        'equipe_b',
        'stade',
        'evenement'
    ).prefetch_related(
        'evenement__zones_tarifs'
    ).order_by('date_heure')[:6]
    
    # Ajouter le prix minimum pour chaque rencontre
    for rencontre in rencontres_a_venir:
        prix_min = rencontre.evenement.zones_tarifs.aggregate(
            prix_min=Min('prix_unitaire')
        )['prix_min']
        rencontre.prix_min = prix_min
    
    # TODO: Récupérer les stars et actualités depuis la base de données
    stars = []
    actualites = []
    
    context = {
        'rencontres_a_venir': rencontres_a_venir,
        'stars': stars,
        'actualites': actualites,
    }
    
    return render(request, 'public/home.html', context)


def match_purchase(request, uid):
    """
    Page de sélection de zone pour un match spécifique.
    """
    rencontre = get_object_or_404(
        Rencontre.objects.select_related(
            'journee__competition',
            'equipe_a',
            'equipe_b',
            'stade',
            'evenement'
        ),
        uid=uid
    )
    
    # Vérifier que le match a une billetterie configurée
    if not rencontre.evenement:
        messages.error(request, "La billetterie n'est pas encore disponible pour ce match.")
        return redirect('public:home')
    
    # Récupérer les zones avec places disponibles
    zones_disponibles = []
    for zone in rencontre.evenement.zones_tarifs.select_related('zone_stade').all():
        # Calculer les places disponibles
        tickets_vendus = zone.tickets.filter(statut__in=['VENDU', 'UTILISE']).count()
        places_disponibles = zone.capacite_max - tickets_vendus
        
        if places_disponibles > 0:
            zones_disponibles.append({
                'zone': zone.zone_stade.nom,
                'prix_unitaire': zone.prix_unitaire,
                'places_disponibles': places_disponibles,
                'zone_obj': zone,
            })
    
    context = {
        'rencontre': rencontre,
        'zones_disponibles': zones_disponibles,
    }
    
    return render(request, 'public/match_purchase.html', context)


def zone_purchase(request, uid, zone_uid):
    """
    Page d'achat de billets pour une zone spécifique.
    """
    rencontre = get_object_or_404(
        Rencontre.objects.select_related(
            'journee__competition',
            'equipe_a',
            'equipe_b',
            'stade',
            'evenement'
        ),
        uid=uid
    )
    
    # Récupérer la zone tarifaire
    zone_tarif = get_object_or_404(
        EvenementZone.objects.select_related('zone_stade'),
        uid=zone_uid,
        evenement=rencontre.evenement
    )
    
    # Calculer les places disponibles
    tickets_vendus = zone_tarif.tickets.filter(statut__in=['VENDU', 'UTILISE']).count()
    places_disponibles = zone_tarif.capacite_max - tickets_vendus
    
    if request.method == 'POST':
        # Traiter l'achat
        quantity = int(request.POST.get('quantity', 1))
        nom = request.POST.get('nom')
        telephone = request.POST.get('telephone')
        email = request.POST.get('email', '')
        
        # Vérifier la disponibilité
        if places_disponibles < quantity:
            messages.error(request, "Nombre de places insuffisant.")
            return redirect('public:zone_purchase', uid=uid, zone_uid=zone_uid)
        
        # Stocker les informations dans la session
        request.session['purchase_data'] = {
            'rencontre_uid': str(uid),
            'zone': zone_tarif.zone_stade.nom,
            'zone_tarif_uid': str(zone_tarif.uid),
            'quantity': quantity,
            'nom': nom,
            'telephone': telephone,
            'email': email,
            'total': float(zone_tarif.prix_unitaire * quantity)
        }
        
        # Stocker l'URL de retour pour le cas d'échec de paiement
        request.session['purchase_return_url'] = request.build_absolute_uri()
        
        return redirect('public:payment_confirmation')
    
    context = {
        'rencontre': rencontre,
        'zone_tarif': zone_tarif,
        'places_disponibles': places_disponibles,
    }
    
    return render(request, 'public/zone_purchase.html', context)


def payment_confirmation(request):
    """
    Page de confirmation de paiement.
    """
    purchase_data = request.session.get('purchase_data')
    
    if not purchase_data:
        messages.error(request, "Aucune commande en cours.")
        return redirect('public:home')
    
    # TODO: Afficher les options de paiement Mobile Money
    
    context = {
        'purchase_data': purchase_data,
    }
    
    return render(request, 'public/payment_confirmation.html', context)



def _construire_session_payment_success(request, vente, notes_data):
    """
    Construit et sauvegarde la session payment_success pour la redirection.
    Fonctionne même si purchase_data est vide dans les notes.
    """
    from infrastructures.models import EvenementZone
    from gouvernance.models.competition import Rencontre

    purchase_data = notes_data.get('purchase_data', {})
    tickets_list = list(vente.tickets.filter(statut='VENDU'))

    # Infos de base depuis la vente
    nom = purchase_data.get('nom') or vente.acheteur_nom or ''
    telephone = purchase_data.get('telephone') or vente.acheteur_telephone or ''
    email = purchase_data.get('email', '')
    quantity = purchase_data.get('quantity') or len(tickets_list) or 1
    total = float(purchase_data.get('total') or vente.montant_total or 0)

    # Infos rencontre/zone
    zone_nom = ''
    rencontre_str = ''
    date_match = ''
    stade = ''

    zone_uid = purchase_data.get('zone_tarif_uid')
    rencontre_uid = purchase_data.get('rencontre_uid')

    try:
        if zone_uid:
            zone = EvenementZone.objects.get(uid=zone_uid)
            zone_nom = zone.zone_stade.nom
        elif tickets_list:
            zone_nom = tickets_list[0].evenement_zone.zone_stade.nom
    except Exception:
        pass

    try:
        if rencontre_uid:
            rencontre = Rencontre.objects.get(uid=rencontre_uid)
            rencontre_str = f"{rencontre.equipe_a.nom_officiel} vs {rencontre.equipe_b.nom_officiel}"
            date_match = rencontre.date_heure.strftime('%d/%m/%Y à %H:%M')
            stade = rencontre.stade.nom
        else:
            # Chercher via l'evenement de la vente
            rencontres = Rencontre.objects.filter(evenement=vente.evenement)
            if rencontres.exists():
                rencontre = rencontres.first()
                rencontre_str = f"{rencontre.equipe_a.nom_officiel} vs {rencontre.equipe_b.nom_officiel}"
                date_match = rencontre.date_heure.strftime('%d/%m/%Y à %H:%M')
                stade = rencontre.stade.nom
    except Exception:
        pass

    request.session['payment_success'] = {
        'vente_uid': str(vente.uid),
        'reference': vente.reference_paiement,
        'nom': nom,
        'telephone': telephone,
        'email': email,
        'quantity': quantity,
        'total': total,
        'payment_method': notes_data.get('methode_paiement', 'Mobile Money'),
        'zone_nom': zone_nom,
        'rencontre': rencontre_str,
        'date_match': date_match,
        'stade': stade,
        'statut_paiement': 'VALIDE',
        'email_envoye': notes_data.get('email_envoye', False),
        'email_destinataire': notes_data.get('email_destinataire', ''),
        'tickets': [
            {
                'uid': str(t.uid),
                'numero': t.numero_billet or str(t.uid)[:8],
                'qr_url': f"/verify/ticket/{t.uid}/"
            }
            for t in tickets_list
        ]
    }
    request.session.save()
    print(f"DEBUG: Session payment_success créée pour vente {vente.uid}")


def _creer_tickets_depuis_purchase_data(vente, notes_data):
    """
    Crée les tickets VENDU pour une vente validée.
    Cherche la zone via purchase_data ou via l'evenement de la vente directement.
    Retourne le nombre de tickets créés.
    """
    from infrastructures.models import Ticket, EvenementZone
    from django.db import transaction
    import json

    quantity = 1
    zone = None

    # Essai 1 : via purchase_data dans les notes
    purchase_data = notes_data.get('purchase_data', {})
    zone_uid = purchase_data.get('zone_tarif_uid')
    if zone_uid:
        try:
            zone = EvenementZone.objects.get(uid=zone_uid)
            quantity = int(purchase_data.get('quantity', 1))
            print(f"TICKETS: Zone trouvée via purchase_data: {zone.zone_stade.nom}")
        except EvenementZone.DoesNotExist:
            zone = None

    # Essai 2 : via l'evenement de la vente (prendre la première zone disponible)
    if zone is None:
        try:
            zones = EvenementZone.objects.filter(evenement=vente.evenement)
            if zones.exists():
                zone = zones.first()
                # Estimer la quantité depuis le montant
                if zone.prix_unitaire and zone.prix_unitaire > 0:
                    quantity = max(1, int(float(vente.montant_total) / float(zone.prix_unitaire)))
                print(f"TICKETS: Zone trouvée via evenement: {zone.zone_stade.nom}, quantité estimée: {quantity}")
        except Exception as e:
            print(f"TICKETS: Erreur recherche zone via evenement: {e}")

    if zone is None:
        print(f"TICKETS: Impossible de trouver une zone pour la vente {vente.uid}")
        return 0

    with transaction.atomic():
        # 1. Chercher tickets EN_RESERVATION liés à cette vente
        tickets_reserve = list(Ticket.objects.filter(
            vente=vente, statut='EN_RESERVATION'
        ).select_for_update()[:quantity])

        if tickets_reserve:
            for t in tickets_reserve:
                t.statut = 'VENDU'
                t.save()
            print(f"TICKETS: {len(tickets_reserve)} tickets EN_RESERVATION → VENDU")
            return len(tickets_reserve)

        # 2. Chercher tickets DISPONIBLE dans la zone
        tickets_dispo = list(Ticket.objects.filter(
            evenement_zone=zone, statut='DISPONIBLE'
        ).select_for_update()[:quantity])

        if tickets_dispo:
            for t in tickets_dispo:
                t.statut = 'VENDU'
                t.vente = vente
                t.save()
            print(f"TICKETS: {len(tickets_dispo)} tickets DISPONIBLE → VENDU")
            return len(tickets_dispo)

        # 3. Créer de nouveaux tickets si aucun disponible
        print(f"TICKETS: Aucun ticket disponible, création de {quantity} nouveaux tickets")
        created = 0
        for _ in range(quantity):
            Ticket.objects.create(
                evenement_zone=zone,
                vente=vente,
                statut='VENDU'
            )
            created += 1
        print(f"TICKETS: {created} nouveaux tickets créés avec statut VENDU")
        return created


def _envoyer_email_billets_apres_paiement(vente, notes_data):
    """
    Envoie l'email avec les billets et QR codes juste après validation du paiement.
    Appelé avant la création de la session de redirection.
    """
    import json
    from django.utils import timezone

    # Ne pas renvoyer si déjà envoyé
    if notes_data.get('email_envoye'):
        print(f"EMAIL: Déjà envoyé précédemment")
        return

    purchase_data = notes_data.get('purchase_data', {})
    email_acheteur = purchase_data.get('email', '').strip()

    if not email_acheteur or '@' not in email_acheteur:
        print(f"EMAIL: Pas d'adresse e-mail valide dans purchase_data")
        return

    try:
        from infrastructures.models import Ticket
        from .email_service import email_service

        tickets_list = list(Ticket.objects.filter(
            vente=vente, statut='VENDU'
        ).select_related('evenement_zone__zone_stade', 'evenement_zone__evenement__infrastructure'))

        if not tickets_list:
            print(f"EMAIL: Aucun ticket VENDU trouvé pour l'envoi")
            return

        print(f"EMAIL: Envoi de {len(tickets_list)} billet(s) à {email_acheteur}")
        result = email_service.envoyer_billet_email(
            email_acheteur,
            vente.acheteur_nom,
            vente,
            tickets_list
        )
        print(f"EMAIL: Résultat = {result}")

        # Marquer comme envoyé dans les notes
        notes_data['email_envoye'] = result.get('success', False)
        notes_data['email_envoye_at'] = timezone.now().isoformat()
        notes_data['email_destinataire'] = email_acheteur
        vente.notes = json.dumps(notes_data)
        vente.save()

    except Exception as e:
        import traceback
        print(f"EMAIL: Erreur lors de l'envoi: {e}")
        print(traceback.format_exc())


def payment_status_api(request):
    """
    API pour vérifier le statut du paiement en temps réel
    Vérifie à la fois la base de données locale ET l'API FlexPay
    """
    from django.http import JsonResponse
    from infrastructures.models import Vente
    import json
    
    # Récupérer les données de la session
    vente_uid = request.session.get('vente_uid')
    order_number = request.session.get('order_number')
    
    # AMÉLIORATION: Si pas de vente_uid, essayer de retrouver par référence de paiement récente
    if not vente_uid:
        # Chercher la vente la plus récente pour cet utilisateur (basé sur l'IP ou session)
        from django.utils import timezone
        from datetime import timedelta
        
        # Chercher les ventes récentes (dernières 30 minutes)
        ventes_recentes = Vente.objects.filter(
            date_vente__gte=timezone.now() - timedelta(minutes=30),
            canal='MOBILE_MONEY'
        ).order_by('-date_vente')[:5]
        
        print(f"DEBUG API STATUS: Pas de vente_uid, recherche parmi {ventes_recentes.count()} ventes récentes")
        
        for vente_test in ventes_recentes:
            notes_data = json.loads(vente_test.notes) if vente_test.notes else {}
            statut_test = notes_data.get('statut_paiement', 'INITIE')
            
            print(f"DEBUG API STATUS: Test vente {vente_test.uid} - Statut: {statut_test}")
            
            if statut_test in ['INITIE', 'VALIDE', 'ECHOUE']:
                # Utiliser cette vente
                vente_uid = str(vente_test.uid)
                print(f"DEBUG API STATUS: ✅ Vente trouvée: {vente_uid}")
                break
    
    if not vente_uid:
        return JsonResponse({
            'success': False,
            'error': 'Session de paiement expirée'
        })
    
    try:
        vente = Vente.objects.get(uid=vente_uid)
        notes_data = json.loads(vente.notes) if vente.notes else {}
        statut_paiement = notes_data.get('statut_paiement', 'INITIE')
        
        # Récupérer le vrai order_number depuis les notes (mis à jour par le thread)
        real_order_number = notes_data.get('order_number', order_number)
        reference_interne = notes_data.get('reference_interne', '')
        
        print(f"DEBUG API STATUS: Vérification pour vente {vente_uid}")
        print(f"  - Statut actuel: {statut_paiement}")
        print(f"  - Order number session: {order_number}")
        print(f"  - Order number réel: {real_order_number}")
        print(f"  - Référence interne: {reference_interne}")
        
        # SI DÉJÀ VALIDE, vérifier si les tickets sont bien créés et retourner immédiatement
        if statut_paiement == 'VALIDE':
            # Vérifier qu'il y a bien des tickets VENDU
            from infrastructures.models import Ticket
            tickets_vendus = Ticket.objects.filter(vente=vente, statut='VENDU').count()
            
            if tickets_vendus > 0:
                print(f"DEBUG API STATUS: Paiement déjà validé avec {tickets_vendus} tickets VENDU")
                response_data = {
                    'success': True,
                    'status': 'VALIDE',
                    'reference': vente.reference_paiement,
                    'tickets_count': tickets_vendus,
                    'message': 'Paiement validé et billets créés'
                }
                return JsonResponse(response_data)
            else:
                print(f"DEBUG API STATUS: Statut VALIDE mais aucun ticket VENDU trouvé")
                # Créer les tickets manquants et la session
                _creer_tickets_depuis_purchase_data(vente, notes_data)
                tickets_vendus = Ticket.objects.filter(vente=vente, statut='VENDU').count()
                if tickets_vendus > 0:
                    _envoyer_email_billets_apres_paiement(vente, notes_data)
                    try:
                        _construire_session_payment_success(request, vente, notes_data)
                    except Exception as e:
                        print(f"DEBUG API STATUS: Erreur session (VALIDE sans tickets): {e}")
                    return JsonResponse({'success': True, 'status': 'VALIDE', 'reference': vente.reference_paiement, 'tickets_count': tickets_vendus})
        
        # Si le statut est INITIE ou ECHOUE (timeout), vérifier auprès de FlexPay
        # Même si le statut est ECHOUE, on vérifie car le paiement peut avoir réussi malgré le timeout
        if statut_paiement in ['INITIE', 'ECHOUE']:
            from django.utils import timezone
            from datetime import timedelta
            
            # Vérifier si assez de temps s'est écoulé pour considérer que le paiement a réussi
            temps_ecoule = timezone.now() - vente.date_vente
            delai_minimal = timedelta(minutes=3)  # 3 minutes minimum
            
            print(f"DEBUG API STATUS: Temps écoulé depuis création: {temps_ecoule}")
            print(f"DEBUG API STATUS: Délai minimal pour validation: {delai_minimal}")
            
            # FORCER LA VALIDATION MANUELLE après 3 minutes si pas de callback
            if temps_ecoule > delai_minimal:
                print(f"DEBUG API STATUS: 🚨 FORCAGE VALIDATION MANUELLE - Temps écoulé > 3 minutes")
                
                # Vérifier si le paiement a déjà été validé manuellement
                if not notes_data.get('validation_manuelle'):
                    print(f"DEBUG API STATUS: Validation manuelle du paiement")
                    
                    # Marquer comme VALIDE manuellement
                    statut_paiement = 'VALIDE'
                    notes_data['statut_paiement'] = 'VALIDE'
                    notes_data['validation_manuelle'] = True
                    notes_data['validation_manuelle_raison'] = 'Timeout API mais validation automatique après délai'
                    notes_data['validation_manuelle_at'] = timezone.now().isoformat()
                    notes_data['temps_ecoule'] = str(temps_ecoule)
                    
                    # CRÉER LES TICKETS si nécessaire
                    from infrastructures.models import Ticket
                    tickets_vendus = Ticket.objects.filter(vente=vente, statut='VENDU').count()
                    
                    if tickets_vendus == 0:
                        print(f"DEBUG API STATUS: Création des tickets après validation manuelle")
                        # Utiliser la logique de création du callback
                        tickets_reserves_uids = notes_data.get('tickets_reserves', [])
                        purchase_data = notes_data.get('purchase_data', {})
                        
                        if tickets_reserves_uids:
                            # Marquer les tickets réservés comme VENDUS
                            from django.db import transaction
                            with transaction.atomic():
                                tickets_reserve = Ticket.objects.filter(uid__in=tickets_reserves_uids, statut='EN_RESERVATION')
                                count_updated = tickets_reserve.update(statut='VENDU', vente=vente)
                                print(f"DEBUG API STATUS: {count_updated} tickets marqués VENDU")

                        # Dans tous les cas, s'assurer qu'il y a des tickets VENDU
                        tickets_vendus_apres = Ticket.objects.filter(vente=vente, statut='VENDU').count()
                        if tickets_vendus_apres == 0:
                            print(f"DEBUG API STATUS: Aucun ticket VENDU, création depuis purchase_data")
                            _creer_tickets_depuis_purchase_data(vente, notes_data)
                    
                    vente.notes = json.dumps(notes_data)
                    vente.save()
                    print(f"DEBUG API STATUS: ✅ Paiement marqué VALIDE manuellement")

                    # ENVOYER L'EMAIL AVANT LA REDIRECTION
                    _envoyer_email_billets_apres_paiement(vente, notes_data)

                    # CRÉER LA SESSION payment_success pour la redirection
                    try:
                        _construire_session_payment_success(request, vente, notes_data)
                    except Exception as e:
                        print(f"DEBUG API STATUS: Erreur création session: {e}")
                else:
                    print(f"DEBUG API STATUS: Déjà validé manuellement précédemment")
                    statut_paiement = 'VALIDE'
            
            else:
                print(f"DEBUG API STATUS: ⏳ Attente - Délai insuffisant pour validation manuelle ({temps_ecoule} < {delai_minimal})")
                
                # Vérifier avec toutes les références disponibles
                references_disponibles = []
                if real_order_number:
                    references_disponibles.append(('order_number', real_order_number))
                if reference_interne:
                    references_disponibles.append(('reference_interne', reference_interne))
                
                if references_disponibles:
                    try:
                        print(f"DEBUG API STATUS: Vérification proactive auprès de FlexPay")
                        print(f"  - Références disponibles: {[ref_type for ref_type, _ in references_disponibles]}")
                        
                        from public.mobile_money_integration import MobileMoneyPaymentProcessor
                        processor = MobileMoneyPaymentProcessor()
                        
                        # Essayer avec chaque référence disponible
                        statut_flexpay = None
                        reference_a_utiliser = None
                        
                        for ref_type, reference_value in references_disponibles:
                            if not reference_value:
                                continue
                                
                            print(f"DEBUG API STATUS: Vérification avec {ref_type}: {reference_value}")
                            
                            if ref_type == 'order_number':
                                statut_flexpay = processor.verifier_paiement(reference_value)
                            else:
                                statut_flexpay = processor.verifier_paiement_par_reference(reference_value)
                            
                            if statut_flexpay and statut_flexpay.get('success'):
                                reference_a_utiliser = reference_value
                                print(f"DEBUG API STATUS: ✅ Succès avec {ref_type}: {reference_value}")
                                break
                            else:
                                print(f"DEBUG API STATUS: ❌ Échec avec {ref_type}: {reference_value}")
                        
                        print(f"DEBUG API STATUS: Résultat final FlexPay: {json.dumps(statut_flexpay, indent=2) if statut_flexpay else 'None'}")
                        
                        if statut_flexpay and statut_flexpay.get('success'):
                            # Mettre à jour le statut local si FlexPay a une réponse
                            flexpay_status = statut_flexpay.get('status')
                            
                            print(f"DEBUG API STATUS: Statut FlexPay: {flexpay_status}")
                            
                            if flexpay_status == 'SUCCESS' or flexpay_status == '0' or flexpay_status == 0 or str(flexpay_status) == '0':
                                statut_paiement = 'VALIDE'
                                notes_data['statut_paiement'] = 'VALIDE'
                                notes_data['flexpay_check'] = statut_flexpay
                                notes_data['flexpay_check_at'] = timezone.now().isoformat()
                                notes_data['reference_verifiee'] = reference_a_utiliser
                                
                                # CRÉER LES TICKETS si nécessaire
                                from infrastructures.models import Ticket
                                tickets_vendus_count = Ticket.objects.filter(vente=vente, statut='VENDU').count()
                                
                                if tickets_vendus_count == 0:
                                    tickets_reserves_uids = notes_data.get('tickets_reserves', [])
                                    if tickets_reserves_uids:
                                        from django.db import transaction
                                        with transaction.atomic():
                                            tickets_reserve = Ticket.objects.filter(uid__in=tickets_reserves_uids, statut='EN_RESERVATION')
                                            tickets_reserve.update(statut='VENDU', vente=vente)
                                            print(f"DEBUG API STATUS: tickets marqués VENDU")

                                    # S'assurer qu'il y a des tickets VENDU dans tous les cas
                                    tickets_vendus_count = Ticket.objects.filter(vente=vente, statut='VENDU').count()
                                    if tickets_vendus_count == 0:
                                        print(f"DEBUG API STATUS: Création tickets depuis purchase_data (FlexPay SUCCESS)")
                                        _creer_tickets_depuis_purchase_data(vente, notes_data)
                                
                                vente.notes = json.dumps(notes_data)
                                vente.save()
                                print(f"DEBUG API STATUS: Paiement marqué VALIDE")
                                
                                # ENVOYER L'EMAIL AVANT LA REDIRECTION
                                _envoyer_email_billets_apres_paiement(vente, notes_data)

                                # CRÉER LA SESSION payment_success pour la redirection
                                try:
                                    _construire_session_payment_success(request, vente, notes_data)
                                except Exception as e:
                                    print(f"DEBUG API STATUS: Erreur création session: {str(e)}")
                                
                            elif flexpay_status == 'FAILED' or flexpay_status == '1' or flexpay_status == 1 or str(flexpay_status) == '1':
                                statut_paiement = 'ECHOUE'
                                notes_data['statut_paiement'] = 'ECHOUE'
                                notes_data['raison_echec'] = statut_flexpay.get('message', 'Paiement échoué')
                                notes_data['flexpay_check'] = statut_flexpay
                                vente.notes = json.dumps(notes_data)
                                vente.save()
                                print(f"DEBUG API STATUS: Paiement marqué ECHOUE")
                                
                            elif flexpay_status == 'CANCELLED' or flexpay_status == 'CANCELED' or flexpay_status == '2' or flexpay_status == 2 or str(flexpay_status) == '2':
                                # NE PAS marquer comme annulé dans les 30 premières secondes
                                # L'utilisateur vient peut-être de recevoir le message
                                from datetime import timedelta
                                temps_ecoule = (timezone.now() - vente.date_vente).total_seconds()
                                
                                if temps_ecoule < 30:
                                    # Trop tôt pour considérer comme annulé - ignorer ce statut
                                    print(f"DEBUG API STATUS: Statut CANCELLED ignoré (seulement {temps_ecoule:.1f}s écoulées)")
                                    # Ne rien faire, garder le statut INITIE
                                else:
                                    # Plus de 30 secondes - vraiment annulé
                                    statut_paiement = 'ECHOUE'
                                    notes_data['statut_paiement'] = 'ECHOUE'
                                    notes_data['raison_echec'] = 'Paiement annulé par l\'utilisateur'
                                    notes_data['message_erreur'] = 'Vous avez annulé le paiement sur votre téléphone'
                                    notes_data['flexpay_check'] = statut_flexpay
                                    vente.notes = json.dumps(notes_data)
                                    vente.save()
                                    print(f"DEBUG API STATUS: Paiement marqué ANNULÉ (après {temps_ecoule:.1f}s)")
                                    
                                    # Libérer les tickets réservés
                                    tickets_reserves_uids = notes_data.get('tickets_reserves', [])
                                    if tickets_reserves_uids:
                                        with transaction.atomic():
                                            from infrastructures.models import Ticket
                                            for ticket_uid in tickets_reserves_uids:
                                                try:
                                                    ticket = Ticket.objects.get(uid=ticket_uid, statut='EN_RESERVATION')
                                                    ticket.statut = 'DISPONIBLE'
                                                    ticket.vente = None
                                                    ticket.save()
                                                except Ticket.DoesNotExist:
                                                    pass
                                        print(f"DEBUG API STATUS: {len(tickets_reserves_uids)} tickets libérés")
                        else:
                            print(f"DEBUG API STATUS: FlexPay n'a retourné aucun succès pour aucune référence")
                            
                    except Exception as e:
                        print(f"Erreur vérification FlexPay: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        # Continuer avec le statut local
                else:
                    print(f"DEBUG API STATUS: Aucune référence disponible pour vérification FlexPay")
        
        response_data = {
            'success': True,
            'status': statut_paiement,
            'reference': vente.reference_paiement,
        }
        
        # Ajouter des détails supplémentaires selon le statut
        if statut_paiement == 'VALIDE':
            from infrastructures.models import Ticket
            tickets_count = Ticket.objects.filter(vente=vente, statut='VENDU').count()
            response_data['tickets_count'] = tickets_count
            response_data['message'] = 'Paiement validé'
        elif statut_paiement == 'ECHOUE':
            response_data['detail'] = notes_data.get('message_erreur', 'Paiement échoué')
        elif statut_paiement == 'EXPIRE':
            response_data['detail'] = 'Réservation expirée'
        
        return JsonResponse(response_data)
        
    except Vente.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Vente non trouvée'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur: {str(e)}'
        })


def get_purchase_return_url(request):
    """
    API pour récupérer l'URL de retour d'achat et rediriger
    """
    from django.http import JsonResponse, HttpResponseRedirect
    
    # Récupérer l'URL de retour stockée dans la session
    return_url = request.session.get('purchase_return_url', '/')
    
    # Rediriger vers l'URL d'achat précédente
    return HttpResponseRedirect(return_url)


def clear_payment_session(request):
    """
    API pour nettoyer la session de paiement échoué
    """
    from django.http import JsonResponse
    
    if request.method == 'POST':
        # Récupérer l'URL de retour AVANT de nettoyer
        return_url = request.session.get('purchase_return_url', '/')
        
        # Nettoyer toutes les données de paiement sauf l'URL de retour
        payment_keys = [
            'vente_uid',
            'order_number', 
            'payment_method',
            'purchase_data',
            'payment_pending',
            'payment_success'
        ]
        
        for key in payment_keys:
            if key in request.session:
                del request.session[key]
        
        # Marquer la session comme modifiée
        request.session.modified = True
        
        return JsonResponse({
            'success': True,
            'message': 'Session de paiement nettoyée',
            'return_url': return_url
        })
    
    return JsonResponse({
        'success': False,
        'error': 'Méthode non autorisée'
    })


def view_ticket(request, ticket_uid):
    """
    Vue pour afficher un ticket spécifique (accessible via QR code ou lien)
    """
    try:
        from infrastructures.models import Ticket
        ticket = Ticket.objects.get(uid=ticket_uid)
        
        context = {
            'ticket': ticket,
            'qr_code': ticket.generer_qr_code(),
            'evenement': ticket.evenement_zone.evenement,
            'zone': ticket.evenement_zone.zone_stade,
        }
        
        return render(request, 'public/ticket_view.html', context)
        
    except Ticket.DoesNotExist:
        return render(request, 'public/ticket_not_found.html', status=404)


def my_tickets(request):
    """
    Vue pour afficher tous les tickets de l'utilisateur
    """
    # Pour l'instant, nous allons afficher les tickets récents
    # Dans une version future, on pourrait ajouter un système d'utilisateurs
    try:
        from infrastructures.models import Ticket
        tickets = Ticket.objects.filter(
            statut='VENDU'
        ).select_related(
            'vente',
            'evenement_zone__evenement',
            'evenement_zone__zone_stade'
        ).order_by('-date_creation')[:20]
        
        context = {
            'tickets': tickets,
        }
        
        return render(request, 'public/my_tickets.html', context)
        
    except Exception as e:
        return render(request, 'public/my_tickets.html', {'tickets': [], 'error': str(e)})


def print_ticket(request, ticket_uid):
    """
    Vue pour imprimer un ticket (version imprimable)
    """
    try:
        from infrastructures.models import Ticket
        ticket = Ticket.objects.get(uid=ticket_uid)
        
        context = {
            'ticket': ticket,
            'qr_code': ticket.generer_qr_code(),
            'evenement': ticket.evenement_zone.evenement,
            'zone': ticket.evenement_zone.zone_stade,
        }
        
        return render(request, 'public/ticket_print.html', context)
        
    except Ticket.DoesNotExist:
        return render(request, 'public/ticket_not_found.html', status=404)


def payment_failed(request):
    """
    Page d'échec de paiement avec gestion spécifique pour solde insuffisant
    """
    # Récupérer les données de la session
    vente_data = request.session.get('vente_data', {})
    reason = request.GET.get('reason', 'autre_erreur')
    detail = request.GET.get('detail', 'Une erreur est survenue lors du paiement')
    
    # Créer un objet vente factice pour l'affichage
    class FakeVente:
        def __init__(self, data):
            self.reference_paiement = data.get('reference_paiement', 'N/A')
            self.montant_total = data.get('total', 0)
            self.methode_paiement = data.get('methode_paiement', 'Mobile Money')
            self.telephone_payeur = data.get('telephone', 'N/A')
    
    vente = FakeVente(vente_data)
    
    context = {
        'vente': vente,
        'reason': reason,
        'detail': detail,
        'vente_data': vente_data
    }
    
    return render(request, 'public/payment_failed.html', context)


def payment_success(request):
    """
    Page de confirmation de paiement réussi.
    """
    payment_success_data = request.session.get('payment_success')
    
    if not payment_success_data:
        messages.error(request, "Aucune confirmation de paiement trouvée.")
        return redirect('public:home')
    
    # Récupérer les tickets réels depuis la base de données
    from infrastructures.models import Ticket, Vente
    
    vente_uid = payment_success_data.get('vente_uid')
    tickets_list = []
    
    if vente_uid:
        try:
            vente = Vente.objects.get(uid=vente_uid)
            tickets_list = list(vente.tickets.filter(statut='VENDU').select_related('evenement_zone__zone_stade', 'evenement_zone__evenement'))
            
            # Mettre à jour les données des tickets avec les QR codes
            payment_success_data['tickets'] = [
                {
                    'uid': str(ticket.uid),
                    'numero': ticket.numero_billet or str(ticket.uid)[:8],
                    'qr_url': f"/verify/ticket/{ticket.uid}/",
                    'qr_code': None  # Le QR code sera généré dans le template ou via une vue dédiée
                }
                for ticket in tickets_list
            ]
            
            # Ajouter le statut de paiement depuis les notes de la vente
            import json
            notes_data = json.loads(vente.notes) if vente.notes else {}
            payment_success_data['statut_paiement'] = notes_data.get('statut_paiement', 'VALIDE')
            payment_success_data['order_number'] = notes_data.get('order_number', '')
            
            # Informer si l'email a déjà été envoyé
            if notes_data.get('email_envoye') and notes_data.get('email_destinataire'):
                payment_success_data['email_envoye'] = True
                payment_success_data['email_destinataire'] = notes_data['email_destinataire']
            
        except Vente.DoesNotExist:
            pass
    
    context = {
        'payment_success': payment_success_data,
        'tickets': tickets_list,  # Passer les objets tickets réels pour le template
    }
    
    # NE PAS nettoyer la session immédiatement pour permettre le rechargement de la page
    # La session sera nettoyée après un certain temps ou lors d'un nouvel achat
    
    return render(request, 'public/payment_success.html', context)


def download_ticket(request, ticket_uid):
    """
    Télécharge un billet unique au format PDF.
    """
    from django.http import HttpResponse
    from django.shortcuts import get_object_or_404
    from infrastructures.models import Ticket
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    import io

    ticket = get_object_or_404(Ticket, uid=ticket_uid)
    numero = ticket.numero_billet or str(ticket.uid)[:8].upper()

    w, h = A4
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    _generer_page_billet(p, ticket, request, w, h)
    p.showPage()
    p.save()

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="billet_{numero}.pdf"'
    return response


def _generer_page_billet(p, ticket, request, w, h):
    """
    Dessine une page billet complète sur le canvas ReportLab.
    Réutilisé par download_ticket et download_vente.
    """
    from reportlab.lib.colors import HexColor, white, black
    from reportlab.lib.utils import ImageReader
    import io
    import qrcode

    bleu_rdc = HexColor('#0036ca')
    jaune_rdc = HexColor('#FDE015')
    gris_clair = HexColor('#f8f9fa')
    gris_texte = HexColor('#555555')

    evenement = ticket.evenement_zone.evenement
    zone = ticket.evenement_zone.zone_stade
    numero = ticket.numero_billet or str(ticket.uid)[:8].upper()

    verify_url = request.build_absolute_uri(f'/verify/ticket/{ticket.uid}/')
    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(verify_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color='black', back_color='white')
    qr_buf = io.BytesIO()
    qr_img.save(qr_buf, format='PNG')
    qr_buf.seek(0)
    qr_reader = ImageReader(qr_buf)

    font = 'Helvetica'

    # Header bleu
    p.setFillColor(bleu_rdc)
    p.rect(0, h - 100, w, 100, fill=1, stroke=0)
    p.setFillColor(white)
    p.setFont(font + '-Bold', 20)
    p.drawString(30, h - 40, 'SI-SEP Sport RDC')
    p.setFont(font, 11)
    p.setFillColor(jaune_rdc)
    p.drawString(30, h - 60, "Billet d'Entrée Officiel")
    p.setFillColor(HexColor('#ffffff33'))
    p.roundRect(w - 160, h - 90, 130, 50, 5, fill=1, stroke=0)
    p.setFillColor(white)
    p.setFont(font, 9)
    p.drawCentredString(w - 95, h - 55, 'Numéro')
    p.setFont(font + '-Bold', 14)
    p.drawCentredString(w - 95, h - 75, numero)

    # Titre événement
    p.setFillColor(black)
    p.setFont(font + '-Bold', 16)
    p.drawString(30, h - 135, evenement.titre)
    p.setStrokeColor(bleu_rdc)
    p.setLineWidth(2)
    p.line(30, h - 145, w - 30, h - 145)

    # Infos événement
    y = h - 175
    for label, valeur in [
        ('Date', evenement.date_evenement.strftime('%d/%m/%Y')),
        ('Lieu', evenement.infrastructure.nom),
        ('Zone', zone.nom),
        ('Prix', f"{ticket.evenement_zone.prix_unitaire:,.0f} CDF"),
    ]:
        p.setFillColor(gris_texte)
        p.setFont(font, 10)
        p.drawString(30, y, label + ' :')
        p.setFillColor(black)
        p.setFont(font + '-Bold', 10)
        p.drawString(160, y, valeur)
        y -= 22

    # QR code
    qr_size = 130
    qr_x = w - qr_size - 30
    qr_y = h - 175 - qr_size + 10
    p.setFillColor(gris_clair)
    p.rect(qr_x - 8, qr_y - 20, qr_size + 16, qr_size + 30, fill=1, stroke=0)
    p.drawImage(qr_reader, qr_x, qr_y, width=qr_size, height=qr_size)
    p.setFillColor(gris_texte)
    p.setFont(font, 8)
    p.drawCentredString(qr_x + qr_size / 2, qr_y - 14, 'Scannez pour vérifier')

    # Séparateur pointillé
    y_sep = h - 330
    p.setStrokeColor(HexColor('#cccccc'))
    p.setLineWidth(1)
    p.setDash(4, 4)
    p.line(30, y_sep, w - 30, y_sep)
    p.setDash()
    p.setFillColor(gris_texte)
    p.setFont(font, 10)
    p.drawString(w / 2 - 5, y_sep - 2, '✂')

    # Infos acheteur
    y = y_sep - 35
    p.setFillColor(bleu_rdc)
    p.setFont(font + '-Bold', 11)
    p.drawString(30, y, "Informations d'achat")
    y -= 20
    achat_infos = []
    if ticket.vente:
        achat_infos = [
            ("Acheté par", ticket.vente.acheteur_nom or 'N/A'),
            ("Téléphone", ticket.vente.acheteur_telephone or 'N/A'),
            ("Date d'achat", ticket.vente.date_vente.strftime('%d/%m/%Y %H:%M')),
            ("Référence", ticket.vente.reference_paiement or 'N/A'),
        ]
    achat_infos.append(("Statut", 'Valide ✓' if ticket.statut == 'VENDU' else ticket.get_statut_display()))
    achat_infos.append(("UID", str(ticket.uid)))
    col2_x = w / 2
    p.setFont(font, 10)
    for i, (label, valeur) in enumerate(achat_infos[:3]):
        row_y = y - i * 22
        p.setFillColor(gris_texte)
        p.drawString(30, row_y, f'{label} :')
        p.setFillColor(black)
        p.setFont(font + '-Bold', 10)
        p.drawString(130, row_y, str(valeur))
        p.setFont(font, 10)
    for i, (label, valeur) in enumerate(achat_infos[3:]):
        row_y = y - i * 22
        p.setFillColor(gris_texte)
        p.drawString(col2_x, row_y, f'{label} :')
        p.setFillColor(black)
        p.setFont(font + '-Bold', 10)
        p.drawString(col2_x + 90, row_y, str(valeur)[:40])
        p.setFont(font, 10)

    # Instructions
    y_inst = y_sep - 175
    p.setFillColor(HexColor('#e3f2fd'))
    p.rect(30, y_inst - 80, w - 60, 90, fill=1, stroke=0)
    p.setStrokeColor(bleu_rdc)
    p.setLineWidth(3)
    p.line(30, y_inst - 80, 30, y_inst + 10)
    p.setFillColor(bleu_rdc)
    p.setFont(font + '-Bold', 10)
    p.drawString(40, y_inst, 'Instructions importantes')
    p.setFillColor(HexColor('#1a3a6b'))
    p.setFont(font, 9)
    for i, line in enumerate([
        "• Présentez ce billet (numérique ou imprimé) à l'entrée du stade",
        "• Le QR code sera scanné pour validation à l'entrée",
        "• Chaque billet est valable pour une seule personne",
        f"• En cas de problème, présentez le numéro : {numero}",
    ]):
        p.drawString(40, y_inst - 18 - i * 14, line)

    # Footer
    p.setFillColor(gris_clair)
    p.rect(0, 0, w, 40, fill=1, stroke=0)
    p.setFillColor(gris_texte)
    p.setFont(font, 8)
    p.drawCentredString(w / 2, 25, 'Billet généré par SI-SEP Sport RDC')
    p.drawCentredString(w / 2, 12, f'Numéro : {numero}  |  UID : {ticket.uid}')


def download_vente(request, vente_uid):
    """
    Télécharge tous les billets d'une vente en un seul PDF multi-pages (1 page = 1 billet).
    """
    from django.http import HttpResponse, HttpResponseNotFound
    from django.shortcuts import get_object_or_404
    from infrastructures.models import Vente
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    import io

    vente = get_object_or_404(Vente, uid=vente_uid)
    tickets = list(vente.tickets.filter(statut='VENDU').select_related(
        'evenement_zone__evenement__infrastructure',
        'evenement_zone__zone_stade',
        'vente',
    ))

    if not tickets:
        return HttpResponseNotFound("Aucun billet valide trouvé pour cette vente.")

    w, h = A4
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    for ticket in tickets:
        _generer_page_billet(p, ticket, request, w, h)
        p.showPage()

    p.save()
    buffer.seek(0)

    ref = vente.reference_paiement or str(vente.uid)[:8]
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="billets_{ref}.pdf"'
    return response


def payment_waiting(request):
    """
    Page d'attente pour Mobile Money avec vérification en temps réel
    """
    from django.shortcuts import render, redirect
    from django.urls import reverse
    from infrastructures.models import Vente
    from django.contrib import messages
    from django.utils import timezone
    from datetime import timedelta
    import json
    
    # Récupérer les données de paiement
    vente_uid = request.session.get('vente_uid')
    order_number = request.session.get('order_number')
    payment_method = request.session.get('payment_method')
    purchase_data = request.session.get('purchase_data')
    
    if not vente_uid or not order_number:
        messages.error(request, "Session de paiement expirée.")
        return redirect('public:home')
    
    try:
        vente = Vente.objects.get(uid=vente_uid)
        
        # IMPORTANT: Vérifier le statut du paiement AVANT l'expiration
        # Car un paiement peut être validé même après le timeout
        notes_data = json.loads(vente.notes) if vente.notes else {}
        statut_paiement = notes_data.get('statut_paiement', 'INITIE')
        
        # Calculer la date limite pour l'expiration
        date_limite = vente.date_vente + timedelta(minutes=15)
        
        # Si le paiement est validé, rediriger vers succès
        if statut_paiement == 'VALIDE':
            # Récupérer les billets déjà créés (statut VENDU)
            from infrastructures.models import Ticket

            # purchase_data peut venir de la session ou des notes de la vente
            if not purchase_data:
                purchase_data = notes_data.get('purchase_data', {})

            # Si pas de tickets VENDU, les créer maintenant
            tickets_list = list(vente.tickets.filter(statut='VENDU'))
            if not tickets_list:
                _creer_tickets_depuis_purchase_data(vente, notes_data)
                tickets_list = list(vente.tickets.filter(statut='VENDU'))
                _creer_tickets_depuis_purchase_data(vente, notes_data)
                tickets_list = list(vente.tickets.filter(statut='VENDU'))

            if tickets_list:
                # ENVOYER L'EMAIL AVANT LA REDIRECTION
                _envoyer_email_billets_apres_paiement(vente, notes_data)

                # Stocker les informations pour la page de succès
                _construire_session_payment_success(request, vente, notes_data)

                # Nettoyer les données de session
                for key in ['vente_uid', 'order_number', 'payment_method', 'purchase_data', 'payment_pending']:
                    if key in request.session:
                        del request.session[key]

                return redirect('public:payment_success')
            else:
                # Si aucun billet trouvé, c'est peut-être un problème de callback
                messages.error(request, "Paiement validé mais billets non générés. Veuillez contacter le support.")
                return redirect('public:home')
        
        # Si échoué, rediriger vers la page d'échec appropriée
        if statut_paiement == 'ECHOUE':
            raison_echec = notes_data.get('raison_echec', 'Paiement échoué')
            message_erreur = notes_data.get('message_erreur', 'Une erreur est survenue lors du paiement')
            
            # Cas spécifique : solde insuffisant
            if raison_echec == 'Solde insuffisant':
                return redirect(f"{reverse('public:payment_failed')}?reason=solde_insuffisant&detail={message_erreur}")
            else:
                return redirect(f"{reverse('public:payment_failed')}?reason=autre_erreur&detail={message_erreur}")
        
        # Cas spécifique : solde insuffisant
        if statut_paiement == 'SOLDE_INSUFFISANT':
            message_erreur = notes_data.get('message_erreur', 'Solde insuffisant pour cette transaction')
            return redirect(f"{reverse('public:payment_failed')}?reason=solde_insuffisant&detail={message_erreur}")
        
        # Cas spécifique : réservation expirée
        if statut_paiement == 'EXPIRE':
            # Nettoyer la session
            for key in ['vente_uid', 'order_number', 'payment_method', 'purchase_data', 'payment_pending']:
                if key in request.session:
                    del request.session[key]
            
            messages.error(request, "Votre réservation a expiré. Veuillez recommencer votre achat.")
            return redirect('public:home')
        
        # Vérifier l'expiration SEULEMENT si le statut est INITIE
        if statut_paiement == 'INITIE':
            date_limite = vente.date_vente + timedelta(minutes=15)
            if timezone.now() > date_limite:
                # La réservation est expirée
                notes_data['statut_paiement'] = 'EXPIRE'
                notes_data['date_expiration'] = timezone.now().isoformat()
                notes_data['raison_expiration'] = 'Timeout de 15 minutes dépassé'
                vente.notes = json.dumps(notes_data)
                vente.save()
                
                # Libérer les tickets associés
                from infrastructures.models import Ticket
                tickets_reserve = Ticket.objects.filter(vente=vente, statut='EN_RESERVATION')
                count_libere = tickets_reserve.update(statut='DISPONIBLE', vente=None)
                
                # Nettoyer la session
                for key in ['vente_uid', 'order_number', 'payment_method', 'purchase_data', 'payment_pending']:
                    if key in request.session:
                        del request.session[key]
                
                messages.error(request, "Votre réservation a expiré. Veuillez recommencer votre achat.")
                return redirect('public:home')
        
        context = {
            'vente': vente,
            'order_number': order_number,
            'payment_method': payment_method,
            'expiration_time': date_limite.strftime('%d/%m/%Y à %H:%M'),
            'remaining_time': max(0, (date_limite - timezone.now()).total_seconds()),
            'purchase_data': purchase_data,
            'statut_paiement': statut_paiement,
        }
        return render(request, 'public/payment_waiting.html', context)
        
    except Vente.DoesNotExist:
        messages.error(request, "Vente non trouvée.")
        return redirect('public:home')
    except Exception as e:
        import traceback
        print(f"ERREUR PAYMENT_WAITING: {e}")
        print(traceback.format_exc())
        messages.error(request, f"Erreur: {str(e)}")
        return redirect('public:home')

def process_payment(request):
    """
    Traite le paiement avec création de billets UNIQUEMENT si paiement confirmé
    """
    from django.shortcuts import redirect
    from django.contrib import messages
    from django.urls import reverse
    from infrastructures.models import Vente, Ticket, EvenementZone
    from gouvernance.models.competition import Rencontre
    from public.mobile_money_integration import MobileMoneyPaymentProcessor
    
    # Vérifier que c'est une requête POST
    if request.method != 'POST':
        messages.error(request, "Méthode non autorisée.")
        return redirect('public:payment_confirmation')
    
    # Récupérer les données d'achat depuis la session
    purchase_data = request.session.get('purchase_data')
    if not purchase_data:
        messages.error(request, "Session d'achat expirée. Veuillez recommencer.")
        return redirect('public:home')
    
    try:
        # Récupérer les objets
        rencontre = Rencontre.objects.get(uid=purchase_data['rencontre_uid'])
        zone = EvenementZone.objects.get(uid=purchase_data['zone_tarif_uid'])
        
        # Récupérer le moyen de paiement
        payment_method = request.POST.get('payment_method')
        payment_phone = request.POST.get('payment_phone', '')
        
        print(f"DEBUG PROCESS_PAYMENT: Méthode={payment_method}, Téléphone={payment_phone}")
        print(f"DEBUG PROCESS_PAYMENT: Purchase data={purchase_data}")
        
        if not payment_method:
            messages.error(request, "Veuillez sélectionner un mode de paiement.")
            return redirect('public:payment_confirmation')
        
        if payment_method == 'EN_LIGNE':
            # Paiement en ligne = succès immédiat
            return _traiter_paiement_en_ligne(request, purchase_data, rencontre, zone)
        
        elif payment_method in ['MPESA', 'ORANGE_MONEY', 'AIRTEL_MONEY']:
            # Mobile Money = initier et attendre validation
            return _traiter_paiement_mobile_money(request, purchase_data, rencontre, zone, payment_method, payment_phone)
        
        else:
            messages.error(request, f"Moyen de paiement non reconnu: {payment_method}")
            return redirect('public:payment_confirmation')
            
    except Rencontre.DoesNotExist:
        messages.error(request, "Rencontre non trouvée.")
        return redirect('public:home')
    except EvenementZone.DoesNotExist:
        messages.error(request, "Zone non trouvée.")
        return redirect('public:home')
    except Exception as e:
        import traceback
        print(f"ERREUR PAIEMENT: {str(e)}")
        print(traceback.format_exc())
        messages.error(request, f"Erreur lors du traitement: {str(e)}")
        return redirect('public:payment_confirmation')

def _traiter_paiement_mobile_money(request, purchase_data, rencontre, zone, methode, telephone):
    """
    Traite le paiement Mobile Money - VERSION SIMPLIFIÉE SANS THREADING
    Appel synchrone à FlexPay avec gestion des timeouts
    """
    from django.contrib import messages
    from django.utils import timezone
    from infrastructures.models import Vente, Ticket
    from django.db import transaction
    from public.mobile_money_integration import MobileMoneyPaymentProcessor
    import uuid
    import json
    
    try:
        with transaction.atomic():
            # Vérifier la disponibilité des tickets avec verrouillage
            tickets_disponibles = list(zone.tickets.filter(
                statut='DISPONIBLE'
            ).select_for_update()[:purchase_data['quantity']])
            
            if len(tickets_disponibles) < purchase_data['quantity']:
                messages.error(request, "Places insuffisantes. Veuillez recommencer.")
                return redirect('public:home')
            
            # Réserver les tickets temporairement (statut EN_RESERVATION)
            tickets_reserves_uids = []
            for ticket in tickets_disponibles:
                ticket.statut = 'EN_RESERVATION'
                ticket.save()
                tickets_reserves_uids.append(str(ticket.uid))
            
            # Créer une référence unique
            reference_interne = f"SISEP-{uuid.uuid4().hex[:8]}-{int(timezone.now().timestamp())}"
            
            # Créer une vente PRÉPAIEMENT
            vente = Vente.objects.create(
                uid=uuid.uuid4(),
                evenement=rencontre.evenement,
                date_vente=timezone.now(),
                montant_total=purchase_data['total'],
                devise='CDF',
                canal='MOBILE_MONEY',
                reference_paiement=f"PAY-{uuid.uuid4().hex[:12].upper()}",
                acheteur_nom=purchase_data['nom'],
                acheteur_telephone=purchase_data['telephone'],
                caissier=None,
                notes=json.dumps({
                    'purchase_data': purchase_data,
                    'statut_paiement': 'INITIE',
                    'tickets_reserves': tickets_reserves_uids,
                    'reference_interne': reference_interne
                })
            )
        
        # Appel SYNCHRONE à FlexPay (pas de threading)
        print(f"🔄 Initiation paiement FlexPay...")
        processor = MobileMoneyPaymentProcessor()
        resultat = processor.initier_paiement(vente, methode, telephone)
        
        # Mettre à jour les notes avec le résultat
        notes_data = json.loads(vente.notes)
        
        if resultat.get('success') and resultat.get('order_number'):
            # Succès - enregistrer le order_number
            notes_data['order_number'] = resultat['order_number']
            notes_data['flexpay_response'] = resultat
            vente.notes = json.dumps(notes_data)
            vente.save()
            
            print(f"✅ Paiement initié: {resultat['order_number']}")
            
            # Stocker dans la session
            request.session['payment_pending'] = True
            request.session['vente_uid'] = str(vente.uid)
            request.session['order_number'] = resultat['order_number']
            request.session['payment_method'] = methode
            request.session['purchase_data'] = purchase_data
            request.session.save()
            
            return redirect('public:payment_waiting')
            
        elif resultat.get('timeout'):
            # Timeout - garder INITIE et rediriger quand même
            notes_data['timeout_initiation'] = resultat.get('error', 'Timeout')
            vente.notes = json.dumps(notes_data)
            vente.save()
            
            print(f"⚠️  Timeout FlexPay - redirection vers page d'attente")
            
            # Stocker dans la session même sans order_number
            request.session['payment_pending'] = True
            request.session['vente_uid'] = str(vente.uid)
            request.session['order_number'] = vente.reference_paiement  # Utiliser la référence de paiement
            request.session['payment_method'] = methode
            request.session['purchase_data'] = purchase_data
            request.session.save()
            
            return redirect('public:payment_waiting')
            
        else:
            # Échec réel
            notes_data['statut_paiement'] = 'ECHOUE'
            notes_data['raison_echec'] = resultat.get('message', 'Erreur inconnue')
            vente.notes = json.dumps(notes_data)
            vente.save()
            
            # Libérer les tickets
            with transaction.atomic():
                for ticket_uid in tickets_reserves_uids:
                    try:
                        ticket = Ticket.objects.get(uid=ticket_uid)
                        ticket.statut = 'DISPONIBLE'
                        ticket.save()
                    except Ticket.DoesNotExist:
                        pass
            
            messages.error(request, f"Erreur d'initiation du paiement: {resultat.get('message')}")
            return redirect('public:payment_confirmation')
        
    except Exception as e:
        import traceback
        print(f"ERREUR PAIEMENT MOBILE MONEY: {e}")
        print(traceback.format_exc())
        messages.error(request, f"Erreur paiement Mobile Money: {str(e)}")
        return redirect('public:payment_confirmation')

def _traiter_paiement_en_ligne(request, purchase_data, rencontre, zone, payment_method='EN_LIGNE'):
    """Traite le paiement en ligne avec création immédiate des billets"""
    from django.utils import timezone
    from django.contrib import messages
    from django.shortcuts import redirect
    from infrastructures.models import Vente, Ticket
    from django.db import transaction
    import uuid
    
    try:
        with transaction.atomic():
            # Vérifier la disponibilité des tickets
            tickets_disponibles = list(zone.tickets.filter(
                statut='DISPONIBLE'
            ).select_for_update()[:purchase_data['quantity']])
            
            if len(tickets_disponibles) < purchase_data['quantity']:
                messages.error(request, "Places insuffisantes. Veuillez recommencer.")
                return redirect('public:home')
            
            # Créer la vente
            vente = Vente.objects.create(
                evenement=rencontre.evenement,
                acheteur_nom=purchase_data['nom'],
                acheteur_telephone=purchase_data['telephone'],
                acheteur_email=purchase_data.get('email', ''),
                montant_total=purchase_data['total'],
                devise='CDF',
                canal='EN_LIGNE',
                statut='CONFIRMEE',
                reference_paiement=f"PAY-{uuid.uuid4().hex[:12].upper()}"
            )
            
            # Attribuer les billets à la vente
            tickets_list = []
            for ticket in tickets_disponibles:
                ticket.statut = 'RESERVE'  # RESERVE au lieu de VENDU
                ticket.vente = vente
                ticket.save()
                tickets_list.append(ticket)
            
            # Stocker les informations pour la page de succès
            request.session['payment_success'] = {
                'vente_uid': str(vente.uid),
                'reference': vente.reference_paiement,
                'nom': purchase_data['nom'],
                'telephone': purchase_data['telephone'],
                'email': purchase_data.get('email', ''),
                'quantity': purchase_data['quantity'],
                'total': float(purchase_data['total']),
                'payment_method': payment_method,
                'zone_nom': zone.zone_stade.nom,
                'rencontre': f"{rencontre.equipe_a.nom_officiel} vs {rencontre.equipe_b.nom_officiel}",
                'date_match': rencontre.date_heure.strftime('%d/%m/%Y à %H:%M'),
                'stade': rencontre.stade.nom,
                'tickets': [
                    {
                        'uid': str(ticket.uid),
                        'numero': str(ticket.uid)[:8],
                        'qr_url': ticket.get_verification_url(request)
                    }
                    for ticket in tickets_list
                ]
            }
        
        # Nettoyer purchase_data
        if 'purchase_data' in request.session:
            del request.session['purchase_data']
        
        messages.success(request, "Paiement effectué avec succès!")
        return redirect('public:payment_success')
        
    except Exception as e:
        import traceback
        print(f"ERREUR PAIEMENT EN LIGNE: {str(e)}")
        print(traceback.format_exc())
        
        # Initier le paiement Mobile Money avec FlexPay
        processor = MobileMoneyPaymentProcessor()
        resultat = processor.initier_paiement(vente, methode, telephone)
        
        if not resultat['success']:
            # Libérer les tickets réservés si échec d'initiation
            with transaction.atomic():
                for ticket_uid in json.loads(vente.notes)['tickets_reserves']:
                    try:
                        ticket = Ticket.objects.get(uid=ticket_uid)
                        ticket.statut = 'DISPONIBLE'
                        ticket.save()
                    except Ticket.DoesNotExist:
                        pass
            vente.delete()
            messages.error(request, f"Erreur d'initialisation: {resultat.get('message', 'Erreur inconnue')}")
            return redirect('public:payment_confirmation')
        
        # Mettre à jour la session avec les infos de paiement
        request.session['payment_pending'] = True
        request.session['vente_uid'] = str(vente.uid)
        request.session['order_number'] = resultat['order_number']
        request.session['payment_method'] = methode
        request.session['purchase_data'] = purchase_data  # Garder les données pour après validation
        request.session.save()
        
        return redirect('public:payment_waiting')
        
    except Exception as e:
        import traceback
        print(f"ERREUR PAIEMENT MOBILE MONEY: {e}")
        print(traceback.format_exc())
        messages.error(request, f"Erreur paiement Mobile Money: {str(e)}")
        return redirect('public:payment_confirmation')
