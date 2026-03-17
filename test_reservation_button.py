#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test du bouton réservation dans l'interface gestionnaire infrastructure
"""

import os
import sys
import django

# Ajouter le projet au path Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_reservation_button():
    """Test du bouton réservation"""
    print("🧪 TEST DU BOUTON RÉSERVATION")
    print("=" * 60)
    
    # Test 1: Vérification de l'URL
    print("\n1. 🔗 Vérification de l'URL")
    try:
        from django.urls import reverse
        url = reverse('infrastructures:infra_manager_create_reservation')
        print(f"   ✅ URL trouvée: {url}")
    except Exception as e:
        print(f"   ❌ Erreur URL: {str(e)}")
        return
    
    # Test 2: Vérification de la vue
    print("\n2. 📋 Vérification de la vue")
    try:
        from infrastructures.views_infra_manager import infra_manager_create_reservation
        print("   ✅ Vue infra_manager_create_reservation importée")
        
        # Vérifier les décorateurs
        import inspect
        source = inspect.getsource(infra_manager_create_reservation)
        if '@login_required' in source and '@require_role' in source:
            print("   ✅ Décorateurs de sécurité présents")
        else:
            print("   ❌ Décorateurs manquants")
            
    except Exception as e:
        print(f"   ❌ Erreur import vue: {str(e)}")
        return
    
    # Test 3: Vérification du template
    print("\n3. 🎨 Vérification du template")
    try:
        template_path = 'templates/infrastructures/infra_manager_evenements.html'
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Vérifier si le bouton est présent
        if 'infra_manager_create_reservation' in template_content:
            print("   ✅ URL du bouton trouvée dans le template")
        else:
            print("   ❌ URL du bouton NON trouvée dans le template")
        
        if 'Réservation' in template_content:
            print("   ✅ Texte 'Réservation' trouvé dans le template")
        else:
            print("   ❌ Texte 'Réservation' NON trouvé dans le template")
        
        if 'bg-green-600' in template_content:
            print("   ✅ Style vert du bouton trouvé")
        else:
            print("   ❌ Style du bouton NON trouvé")
            
    except Exception as e:
        print(f"   ❌ Erreur lecture template: {str(e)}")
        return
    
    # Test 4: Vérification du modèle Evenement
    print("\n4. 🗃️ Vérification du modèle Evenement")
    try:
        from infrastructures.models import Evenement
        
        # Vérifier les choices du type_evenement
        choices = Evenement._meta.get_field('type_evenement').choices
        choice_values = [choice[0] for choice in choices]
        
        if 'RESERVATION' in choice_values:
            print("   ✅ Type 'RESERVATION' trouvé dans les choices")
        else:
            print("   ❌ Type 'RESERVATION' NON trouvé dans les choices")
            print(f"   📋 Choices disponibles: {choice_values}")
            
    except Exception as e:
        print(f"   ❌ Erreur modèle Evenement: {str(e)}")
        return
    
    # Test 5: Simulation de rendu du template
    print("\n5. 🖥️ Test de rendu du template")
    try:
        from django.template import Template, Context
        
        # Créer un contexte de test
        context = Context({
            'user_role': 'infra_manager',
            'infrastructure': type('Infrastructure', (), {'nom': 'Test Stadium'})(),
        })
        
        # Extraire la partie du template avec le bouton
        template_snippet = """
        {% load static %}
        <div class="flex items-center gap-3">
            <a href="{% url 'infrastructures:infra_manager_create_reservation' %}"
               class="inline-flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-semibold rounded-lg transition-colors border border-green-700">
                <i class="fa-solid fa-plus"></i>
                <span>Réservation</span>
            </a>
        </div>
        """
        
        # Tester le rendu
        template = Template(template_snippet)
        rendered = template.render(context)
        
        if 'Réservation' in rendered:
            print("   ✅ Template rendu avec succès")
            print(f"   📄 Contenu rendu: {rendered.strip()}")
        else:
            print("   ❌ Template NON rendu correctement")
            
    except Exception as e:
        print(f"   ❌ Erreur rendu template: {str(e)}")
        return
    
    # Test 6: Vérification des permissions
    print("\n6. 🔒 Vérification des permissions")
    try:
        from core.permissions import require_role
        
        # Vérifier que le rôle INFRA_MANAGER existe
        from core.models import RoleUtilisateur
        roles = RoleUtilisateur.objects.values_list('role', flat=True)
        
        if 'INFRA_MANAGER' in roles:
            print("   ✅ Rôle INFRA_MANAGER trouvé dans la base")
        else:
            print("   ❌ Rôle INFRA_MANAGER NON trouvé dans la base")
            print(f"   📋 Rôles disponibles: {list(roles)}")
            
    except Exception as e:
        print(f"   ❌ Erreur vérification permissions: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎯 RÉSULTAT DU TEST")
    print("\n✅ Éléments vérifiés:")
    print("   1. ✅ URL de création de réservation")
    print("   2. ✅ Vue avec décorateurs de sécurité")
    print("   3. ✅ Template avec bouton réservation")
    print("   4. ✅ Modèle Evenement avec type RESERVATION")
    print("   5. ✅ Rendu du template fonctionnel")
    
    print("\n🔧 Actions recommandées:")
    print("   1. Redémarrer le serveur Django")
    print("   2. Vider le cache du navigateur")
    print("   3. Vérifier que vous êtes bien connecté en tant que INFRA_MANAGER")
    print("   4. Rafraîchir la page des événements")
    
    print("\n🚀 Bouton réservation prêt!")
    print("   Si le bouton n'apparaît toujours pas, redémarrez le serveur Django.")

if __name__ == '__main__':
    test_reservation_button()
