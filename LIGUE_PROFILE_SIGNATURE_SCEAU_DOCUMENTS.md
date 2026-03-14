# Mise à jour du Profil de la Ligue - Signature, Cachet et Documents Officiels

## Résumé des modifications

L'interface "Mon Profil" du secrétaire de la ligue a été complètement refactorisée pour :
1. Ressembler à celle du Secrétaire Général avec les sections d'upload de signature et cachet
2. Afficher les documents officiels de la ligue (Attestation d'Homologation)
3. Centraliser toutes les informations importantes en un seul endroit

## Changements effectués

### 1. Modèle (gouvernance/models/institution.py)
Ajout de deux nouveaux champs au modèle `Institution` :
- `signature_image` : ImageField pour la signature numérique (PNG transparent)
- `sceau_image` : ImageField pour le cachet/sceau (PNG transparent)

Ces champs sont disponibles pour les Ligues et Fédérations.

### 2. Migration
Création de la migration `0028_add_signature_sceau_to_institution.py` qui ajoute les deux champs à la table `institution`.

### 3. Vue (gouvernance/views_ligue_secretary.py)
Modification de la fonction `ligue_profile()` pour :
- Traiter les requêtes POST pour les uploads de signature et cachet
- Vérifier le mot de passe de l'utilisateur avant de permettre les modifications
- Valider que les fichiers sont des PNG et ne dépassent pas 5MB
- Afficher les messages de succès/erreur appropriés
- Récupérer et afficher l'attestation d'homologation

### 4. Template (templates/gouvernance/ligue_profile.html)
Refonte complète du template pour :
- Ajouter les sections "Signature" et "Cachet Personnel" avec upload
- Implémenter les mêmes styles et interactions que le profil SG
- Ajouter les modales de confirmation par mot de passe
- Ajouter une section "Documents Officiels" en bas avec :
  - Statut d'Agrément
  - Attestation d'Homologation (téléchargeable)
  - Informations officielles de la ligue
  - Conseils utiles
- Conserver les sections existantes (Informations, Adresse, Attestation, Disciplines, Fédération)

## Fonctionnalités

### Upload de Signature et Cachet
- Interface drag-and-drop intuitive
- Validation des fichiers PNG uniquement
- Limite de taille : 5MB
- Confirmation par mot de passe pour la sécurité
- Affichage de l'aperçu du fichier actuel

### Documents Officiels
- Affichage du statut d'agrément (Agréée / En Attente)
- Téléchargement de l'Attestation d'Homologation
- Affichage du code officiel et de la province
- Informations utiles sur les documents

### Sécurité
- Vérification du mot de passe avant toute modification
- Validation des types de fichiers
- Vérification de la taille des fichiers
- Messages d'erreur clairs

### Interface
- Design cohérent avec le profil SG
- Utilisation de la charte graphique RDC (couleurs bleu royal)
- Responsive et accessible
- Modales de confirmation élégantes

## Utilisation

1. Le secrétaire de la ligue accède à son profil via le menu "Documents Officiels"
2. Il peut voir les sections "Signature" et "Cachet Personnel" en haut
3. Il peut voir les documents officiels de la ligue en bas
4. Il peut télécharger l'Attestation d'Homologation
5. Il peut mettre à jour sa signature et son cachet en cliquant sur les zones d'upload

## Fichiers modifiés

- `gouvernance/models/institution.py` - Ajout des champs
- `gouvernance/migrations/0028_add_signature_sceau_to_institution.py` - Migration
- `gouvernance/views_ligue_secretary.py` - Logique d'upload
- `templates/gouvernance/ligue_profile.html` - Interface utilisateur

## Notes

- Les fichiers PNG doivent être transparents pour un meilleur rendu
- La taille recommandée pour les signatures est 200x100px
- La taille recommandée pour les cachets est 200x200px (carrés)
- Les fichiers sont stockés dans `media/institutions/signatures/` et `media/institutions/sceaux/`
- L'Attestation d'Homologation est affichée si elle existe dans la base de données
