#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour corriger un paiement validé sans tickets ni purchase_data
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from infrastructures.models import Vente, Ticket, EvenementZone
from gouvernance.models import Rencontre
from django.utils import timezone
from django.db import transaction
import json
import uuid

def fix_payment_missing_data():
    """Corriger le paiement validé sans données"""
    
    reference = '94qotgMn36g5243840690816-SISEP-ecf3fac4-1773727207'
    
    try:
        vente = Vente.objects.get(reference_paiement=reference)
        print(f"✅ Vente trouvée: {vente.uid}")
        print(f"   Référence: {vente.reference_paiement}")
        print(f"   Acheteur: {vente.acheteur_nom} ({vente.acheteur_telephone})")
        print(f"   Montant: {vente.montant_total} CDF")
        
        # Vérifier les notes
        notes_data = json.loads(vente.notes) if vente.notes else {}
        statut_paiement = notes_data.get('statut_paiement', 'INITIE')
        print(f"\n📊 Statut actuel: {statut_paiement}")
        
        # Vérifier si purchase_data existe
        purchase_data = notes_data.get('purchase_data')
        if not purchase_data:
            print(f"\n❌ Pas de purchase_data - impossible de créer les tickets automatiquement")
            print(f"   Il faut connaître:")
            print(f"   - La rencontre (rencontre_uid)")
            print(f"   - La zone (zone_tarif_uid)")
            print(f"   - La quantité de billets")
            
            # Essayer de deviner depuis l'événement
            if vente.evenement:
                print(f"\n🔍 Événement trouvé: {vente.evenement.titre}")
                
                # Chercher la rencontre associée
                rencontres = Rencontre.objects.filter(evenement=vente.evenement)
                if rencontres.exists():
                    rencontre = rencontres.first()
                    print(f"✅ Rencontre trouvée: {rencontre.equipe_a.nom_officiel} vs {rencontre.equipe_b.nom_officiel}")
                    
                    # Chercher les zones disponibles
                    zones = vente.evenement.zones_tarifs.all()
                    print(f"✅ Zones disponibles: {zones.count()}")
                    
                    for zone in zones:
                        print(f"   - {zone.zone_stade.nom}: {zone.prix_unitaire} CDF")
                    
                    # Deviner la zone basée sur le montant
                    quantite_probable = 1  # Par défaut 1 billet
                    zone_probable = None
                    
                    for zone in zones:
                        if abs(zone.prix_unitaire * quantite_probable - vente.montant_total) < 1:
                            zone_probable = zone
                            break
                    
                    if zone_probable:
                        print(f"\n💡 Zone probable: {zone_probable.zone_stade.nom} (prix: {zone_probable.prix_unitaire} CDF)")
                        print(f"   Quantité probable: {quantite_probable}")
                        
                        # Demander confirmation
                        print(f"\n⚠️  ATTENTION: Création automatique des données manquantes")
                        print(f"   Rencontre: {rencontre.equipe_a.nom_officiel} vs {rencontre.equipe_b.nom_officiel}")
                        print(f"   Zone: {zone_probable.zone_stade.nom}")
                        print(f"   Quantité: {quantite_probable}")
                        print(f"   Montant: {vente.montant_total} CDF")
                        
                        # Créer les purchase_data
                        purchase_data = {
                            'rencontre_uid': str(rencontre.uid),
                            'zone': zone_probable.zone_stade.nom,
                            'zone_tarif_uid': str(zone_probable.uid),
                            'quantity': quantite_probable,
                            'nom': vente.acheteur_nom,
                            'telephone': vente.acheteur_telephone,
                            'email': '',  # Pas de champ email dans le modèle Vente
                            'total': float(vente.montant_total)
                        }
                        
                        # Créer les tickets
                        with transaction.atomic():
                            # Vérifier la disponibilité
                            tickets_disponibles = list(zone_probable.tickets.filter(
                                statut='DISPONIBLE'
                            ).select_for_update()[:quantite_probable])
                            
                            if len(tickets_disponibles) >= quantite_probable:
                                print(f"\n✅ {len(tickets_disponibles)} tickets disponibles")
                                
                                # Créer les tickets
                                tickets_crees = []
                                for ticket in tickets_disponibles:
                                    ticket.statut = 'VENDU'
                                    ticket.vente = vente
                                    ticket.date_vente = vente.date_vente
                                    # Générer un numéro de billet unique (max 12 caractères)
                                    ticket.numero_billet = f"{ticket.uid.hex[:12].upper()}"
                                    ticket.save()
                                    tickets_crees.append(ticket)
                                    print(f"   ✅ Ticket créé: {ticket.numero_billet}")
                                
                                # Mettre à jour les notes
                                notes_data['purchase_data'] = purchase_data
                                notes_data['tickets_crees_manuellement'] = True
                                notes_data['tickets_crees_at'] = timezone.now().isoformat()
                                notes_data['correction_manuelle'] = 'Données manquantes ajoutées automatiquement'
                                vente.notes = json.dumps(notes_data)
                                vente.save()
                                
                                print(f"\n✅ Paiement corrigé avec succès!")
                                print(f"   - Purchase data ajouté")
                                print(f"   - {len(tickets_crees)} tickets créés")
                                print(f"   - Statut: {statut_paiement}")
                                
                                return True
                            else:
                                print(f"\n❌ Pas assez de tickets disponibles ({len(tickets_disponibles)} < {quantite_probable})")
                    else:
                        print(f"\n❌ Impossible de deviner la zone (montant: {vente.montant_total} CDF)")
                else:
                    print(f"❌ Aucune rencontre trouvée pour cet événement")
            else:
                print(f"❌ Pas d'événement associé à cette vente")
        else:
            print(f"✅ Purchase data existe déjà")
            
            # Vérifier les tickets
            tickets_vendus = vente.tickets.filter(statut='VENDU').count()
            if tickets_vendus == 0:
                print(f"\n⚠️  Aucun ticket VENDU - création nécessaire")
                
                # Créer les tickets depuis purchase_data
                try:
                    rencontre = Rencontre.objects.get(uid=purchase_data['rencontre_uid'])
                    zone = EvenementZone.objects.get(uid=purchase_data['zone_tarif_uid'])
                    quantite = purchase_data['quantity']
                    
                    with transaction.atomic():
                        tickets_disponibles = list(zone.tickets.filter(
                            statut='DISPONIBLE'
                        ).select_for_update()[:quantite])
                        
                        if len(tickets_disponibles) >= quantite:
                            for ticket in tickets_disponibles:
                                ticket.statut = 'VENDU'
                                ticket.vente = vente
                                ticket.date_vente = vente.date_vente
                                ticket.numero_billet = f"{ticket.uid.hex[:12].upper()}"
                                ticket.save()
                                print(f"   ✅ Ticket créé: {ticket.numero_billet}")
                            
                            print(f"\n✅ {len(tickets_disponibles)} tickets créés avec succès!")
                            return True
                        else:
                            print(f"\n❌ Pas assez de tickets disponibles")
                except Exception as e:
                    print(f"\n❌ Erreur création tickets: {e}")
            else:
                print(f"✅ {tickets_vendus} tickets VENDU déjà créés")
                return True
        
        return False
        
    except Vente.DoesNotExist:
        print(f"❌ Vente non trouvée: {reference}")
        return False
    except Exception as e:
        import traceback
        print(f"❌ Erreur: {e}")
        print(traceback.format_exc())
        return False

if __name__ == '__main__':
    fix_payment_missing_data()
