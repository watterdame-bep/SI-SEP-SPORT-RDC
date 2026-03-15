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



def payment_success(request):
    """
    Page de confirmation de paiement réussi.
    """
    payment_success = request.session.get('payment_success')
    
    if not payment_success:
        return redirect('public:home')
    
    # Générer les QR codes pour chaque ticket
    for ticket_data in payment_success.get('tickets', []):
        if 'qr_url' in ticket_data and not ticket_data.get('qr_code_generated'):
            # Générer le QR code ici si nécessaire
            # Pour l'instant, on utilise juste l'URL
            pass
    
    context = {
        'payment_success': payment_success,
    }
    
    # Nettoyer la session après affichage
    if 'payment_success' in request.session:
        del request.session['payment_success']
    
    return render(request, 'public/payment_success.html', context)

def payment_waiting(request):
    """
    Page d'attente pour Mobile Money
    """
    from django.shortcuts import render
    from infrastructures.models import Vente
    
    # Récupérer les données de paiement
    vente_uid = request.session.get('vente_uid')
    order_number = request.session.get('order_number')
    payment_method = request.session.get('payment_method')
    purchase_data = request.session.get('purchase_data')
    
    if not vente_uid or not order_number:
        from django.contrib import messages
        messages.error(request, "Session de paiement expirée.")
        return redirect('home')
    
    try:
        vente = Vente.objects.get(uid=vente_uid)
        context = {
            'vente': vente,
            'order_number': order_number,
            'payment_method': payment_method,
            'purchase_data': purchase_data,
        }
        return render(request, 'public/payment_waiting.html', context)
    except Vente.DoesNotExist:
        from django.contrib import messages
        messages.error(request, "Vente non trouvée.")
        return redirect('home')

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
        
        print(f"DEBUG: Paiement {payment_method} pour {payment_phone}")
        
        if payment_method == 'EN_LIGNE':
            # Paiement en ligne = succès immédiat
            return _traiter_paiement_en_ligne(request, purchase_data, rencontre, zone)
        
        elif payment_method in ['MPESA', 'ORANGE_MONEY', 'AIRTEL_MONEY']:
            # Mobile Money = initier et attendre validation
            return _traiter_paiement_mobile_money(request, purchase_data, rencontre, zone, payment_method, payment_phone)
        
        else:
            messages.error(request, "Moyen de paiement non reconnu.")
            return redirect('public:payment_confirmation')
            
    except Exception as e:
        import traceback
        print(f"ERREUR PAIEMENT: {str(e)}")
        print(traceback.format_exc())
        messages.error(request, f"Erreur lors du traitement: {str(e)}")
        return redirect('public:payment_confirmation')

def _traiter_paiement_mobile_money(request, purchase_data, rencontre, zone, methode, telephone):
    """
    Traite le paiement Mobile Money SANS créer les billets
    Les billets seront créés UNIQUEMENT après validation du paiement
    """
    from django.contrib import messages
    from django.utils import timezone
    from infrastructures.models import Vente
    import uuid
    
    try:
        # Créer une vente PRÉPAIEMENT (sans billets)
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
            caissier=None,  # Pas de caissier pour Mobile Money
            # Pas de billets créés pour le moment
        )
        
        # Initier le paiement Mobile Money
        processor = MobileMoneyPaymentProcessor()
        resultat = processor.initier_paiement(vente, methode, telephone)
        
        if not resultat['success']:
            # Supprimer la vente si échec d'initiation
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
                ticket.statut = 'VENDU'
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
        messages.error(request, f"Erreur paiement en ligne: {str(e)}")
        return redirect('public:payment_confirmation')

def _traiter_paiement_mobile_money(request, purchase_data, rencontre, zone, methode, telephone):
    """
    Traite le paiement Mobile Money SANS créer les billets
    Les billets seront créés UNIQUEMENT après validation du paiement
    """
    from django.contrib import messages
    from django.utils import timezone
    from infrastructures.models import Vente
    import uuid
    
    try:
        # Créer une vente PRÉPAIEMENT (sans billets)
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
            caissier='SYSTEM',
            # Pas de billets créés pour le moment
        )
        
        # Initier le paiement Mobile Money
        processor = MobileMoneyPaymentProcessor()
        resultat = processor.initier_paiement(vente, methode, telephone)
        
        if not resultat['success']:
            # Supprimer la vente si échec d'initiation
            vente.delete()
            messages.error(request, f"Erreur d'initialisation: {resultat.get('message', 'Erreur inconnue')}")
            return redirect('payment_confirmation')
        
        # Mettre à jour la session avec les infos de paiement
        request.session['payment_pending'] = True
        request.session['vente_uid'] = str(vente.uid)
        request.session['order_number'] = resultat['order_number']
        request.session['payment_method'] = methode
        request.session['purchase_data'] = purchase_data  # Garder les données pour après validation
        request.session.save()
        
        return redirect('payment_waiting')
        
    except Exception as e:
        print(f"ERREUR PAIEMENT MOBILE MONEY: {e}")
        messages.error(request, f"Erreur paiement Mobile Money: {str(e)}")
        return redirect('payment_confirmation')
