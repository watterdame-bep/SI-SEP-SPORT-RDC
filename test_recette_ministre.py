#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test de la recette totale pour le dashboard du ministre
"""

import os
import sys
import django

# Ajouter le projet au path Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from infrastructures.models import Vente
from datetime import datetime
import json

def test_recette_annee():
    """Test du calcul de la recette annuelle"""
    print("🧪 TEST DE LA RECETTE ANNUELLE")
    print("=" * 40)
    
    annee_courante = datetime.now().year
    print(f"Année courante: {annee_courante}")
    
    # Calcul de la recette totale en vérifiant le statut dans les notes
    ventes_annee = Vente.objects.filter(date_vente__year=annee_courante)
    
    recette_totale = 0
    ventes_valides = 0
    
    for vente in ventes_annee:
        try:
            if vente.notes:
                notes_data = json.loads(vente.notes)
                statut = notes_data.get('statut_paiement', 'INITIE')
                if statut == 'VALIDE':
                    recette_totale += float(vente.montant_total)
                    ventes_valides += 1
        except (json.JSONDecodeError, TypeError):
            # Si les notes ne sont pas valides, on considère la vente comme valide
            recette_totale += float(vente.montant_total)
            ventes_valides += 1
    
    print(f"Recette totale {annee_courante}: {recette_totale:,.0f} CDF")
    print(f"Nombre de ventes validées: {ventes_valides}")
    
    # Détail par mois
    print("\n📊 RECETTE PAR MOIS:")
    for mois in range(1, 13):
        ventes_mois = Vente.objects.filter(
            date_vente__year=annee_courante,
            date_vente__month=mois
        )
        
        recette_mois = 0
        for vente in ventes_mois:
            try:
                if vente.notes:
                    notes_data = json.loads(vente.notes)
                    statut = notes_data.get('statut_paiement', 'INITIE')
                    if statut == 'VALIDE':
                        recette_mois += float(vente.montant_total)
            except (json.JSONDecodeError, TypeError):
                recette_mois += float(vente.montant_total)
        
        if recette_mois > 0:
            nom_mois = datetime(annee_courante, mois, 1).strftime('%B')
            print(f"  {nom_mois}: {recette_mois:,.0f} CDF")
    
    # Top 5 des ventes
    print("\n🏆 TOP 5 DES VENTES:")
    top_ventes = []
    for vente in ventes_annee:
        try:
            if vente.notes:
                notes_data = json.loads(vente.notes)
                statut = notes_data.get('statut_paiement', 'INITIE')
                if statut == 'VALIDE':
                    top_ventes.append(vente)
        except (json.JSONDecodeError, TypeError):
            top_ventes.append(vente)
    
    top_ventes.sort(key=lambda x: x.montant_total, reverse=True)
    top_ventes = top_ventes[:5]
    
    for i, vente in enumerate(top_ventes, 1):
        print(f"  {i}. {vente.reference_paiement}: {vente.montant_total:,.0f} CDF")
    
    # Statistiques générales
    print(f"\n📈 STATISTIQUES:")
    print(f"  Nombre total de ventes validées: {ventes_valides}")
    print(f"  Montant moyen: {recette_totale / ventes_valides:,.0f} CDF" if ventes_valides > 0 else "  Montant moyen: 0 CDF")
    print(f"  Recette totale: {recette_totale:,.0f} CDF")

if __name__ == '__main__':
    test_recette_annee()
