# Séparation des Interfaces - Profil et Documents Officiels de la Ligue

## Résumé des modifications

L'interface du secrétaire de ligue a été séparée en deux sections distinctes :
1. **Mon Profil** - Gestion de la signature et du cachet personnel
2. **Documents Officiels** - Affichage des documents d'agrément et d'homologation

## Changements effectués

### 1. Nouvelle Route (gouvernance/urls.py)
Ajout de la route `ligue_documents` :
```python
path('ligue/documents/', views_ligue_secretary.ligue_documents, name='ligue_documents'),
```

### 2. Nouvelle Vue (gouvernance/views_ligue_secretary.py)
Création de la fonction `ligue_documents()` qui :
- Récupère la ligue du profil utilisateur
- Récupère l'attestation d'homologation
- Affiche le template `ligue_documents.html`

### 3. Nouveau Template (templates/gouvernance/ligue_documents.html)
Création d'un template dédié aux documents officiels qui affiche :
- Statut d'Agrément (Agréée / En Attente)
- Attestation d'Homologation avec téléchargement
- Informations officielles de la ligue
- Conseils utiles

### 4. Mise à jour du Sidebar (templates/core/base.html)
Modification du sidebar du secrétaire de ligue :
- **Documents Officiels** → pointe vers `ligue_documents`
- **Mon Profil** → pointe vers `ligue_profile` (nouveau lien)

### 5. Nettoyage du Template Profil (templates/gouvernance/ligue_profile.html)
Suppression de la section "Documents Officiels" du template profil pour ne garder que :
- Informations de la ligue
- Signature et Cachet Personnel
- Adresse de contact
- Attestation d'homologation (info seulement)
- Disciplines
- Fédération parente

## Navigation

### Sidebar du Secrétaire de Ligue
```
DOCUMENTS
├── Documents Officiels → ligue_documents (affiche les documents)
└── Mon Profil → ligue_profile (gestion signature/cachet)
```

## Interfaces

### Mon Profil (ligue_profile)
- Informations de la ligue
- Upload de signature (PNG transparent, max 5MB)
- Upload de cachet (PNG transparent, max 5MB)
- Confirmation par mot de passe
- Adresse de contact
- Disciplines
- Fédération parente

### Documents Officiels (ligue_documents)
- Statut d'Agrément
- Attestation d'Homologation (téléchargeable)
- Informations officielles
- Conseils utiles

## Fichiers modifiés

- `gouvernance/urls.py` - Ajout de la route `ligue_documents`
- `gouvernance/views_ligue_secretary.py` - Ajout de la vue `ligue_documents`
- `templates/gouvernance/ligue_documents.html` - Nouveau template
- `templates/gouvernance/ligue_profile.html` - Suppression de la section documents
- `templates/core/base.html` - Mise à jour du sidebar

## Sécurité

- Vérification du rôle `FEDERATION_SECRETARY` pour accéder aux deux interfaces
- Vérification que l'utilisateur est associé à une ligue
- Confirmation par mot de passe pour les uploads de signature/cachet
- Validation des fichiers PNG (max 5MB)
