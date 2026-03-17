#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Génère les numéros de billets pour les tickets existants
"""

import os
import sys
import django

# Ajouter le projet au path Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from infrastructures.models import Ticket

def generate_missing_ticket_numbers():
    """Génère les numéros de billets manquants"""
    print("🔧 GÉNÉRATION DES NUMÉROS DE BILLETS MANQUANTS")
    print("=" * 50)
    
    tickets_sans_numero = Ticket.objects.filter(numero_billet__isnull=True)
    total_tickets = tickets_sans_numero.count()
    
    if total_tickets == 0:
        print("✅ Tous les tickets ont déjà un numéro!")
        return
    
    print(f"📝 {total_tickets} tickets sans numéro trouvés")
    
    success_count = 0
    error_count = 0
    
    for i, ticket in enumerate(tickets_sans_numero, 1):
        try:
            # Générer un numéro unique
            numero = ticket.generer_numero_billet()
            ticket.numero_billet = numero
            ticket.save()
            
            print(f"   ✅ [{i}/{total_tickets}] Ticket {str(ticket.uid)[:8]}... → {numero}")
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ [{i}/{total_tickets}] Erreur ticket {str(ticket.uid)[:8]}...: {str(e)}")
            error_count += 1
    
    print("\n" + "=" * 50)
    print("📊 RÉSULTATS:")
    print(f"   ✅ Succès: {success_count}")
    print(f"   ❌ Erreurs: {error_count}")
    print(f"   📈 Total traité: {success_count + error_count}")
    
    if error_count == 0:
        print("\n🎉 Tous les numéros ont été générés avec succès!")
    else:
        print(f"\n⚠️ {error_count} tickets n'ont pas pu être mis à jour")

if __name__ == '__main__':
    generate_missing_ticket_numbers()
