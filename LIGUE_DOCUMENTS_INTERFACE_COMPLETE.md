# Interface Documents Officiels de la Ligue - Implémentation Complète

## Résumé

L'interface "Documents Officiels" du secrétaire de la ligue a été créée pour ressembler à celle de la fédération, affichant l'Attestation d'Homologation et les informations officielles de la ligue.

## Fichiers créés/modifiés

### 1. Template (templates/gouvernance/ligue_documents.html)
Nouveau template créé avec :
- **En-tête** : Titre et description de la ligue
- **Statut d'Agrément** : Affichage du statut (Agréée / En Attente)
- **Grille de documents** :
  - Attestation d'Homologation (téléchargeable)
  - Informations Officielles (nom, sigle, statut, email)
- **Informations Utiles** : Conseils sur l'utilisation des documents

### 2. Vue (gouvernance/views_ligue_secretary.py)
La vue `ligue_documents()` existante :
- Récupère la ligue du profil utilisateur
- Récupère l'Attestation d'Homologation
- Passe les données au template

### 3. URLs (gouvernance/urls.py)
Route déjà configurée :
- `path('ligue/documents/', views_ligue_secretary.ligue_documents, name='ligue_documents')`

### 4. Sidebar (templates/core/base.html)
Lien déjà configuré :
- Pointe vers `ligue_documents`
- Affiche "Documents Officiels"

## Fonctionnalités

### Statut d'Agrément
- Affichage du statut (Agréée / En Attente)
- Numéro d'homologation
- Code officiel
- Province

### Attestation d'Homologation
- Numéro d'attestation
- Date d'approbation
- Validité
- Téléchargement du document

### Informations Officielles
- Nom officiel de la ligue
- Sigle
- Statut (Active / Inactive)
- Email officiel

### Informations Utiles
- Conseils sur l'utilisation des documents
- Importance de la conservation
- Utilisation pour dossiers administratifs

## Design

- Utilise la charte graphique RDC (couleurs bleu royal)
- Responsive et accessible
- Cohérent avec l'interface de la fédération
- Icônes Font Awesome pour meilleure UX

## Utilisation

1. Le secrétaire de la ligue clique sur "Documents Officiels" dans le sidebar
2. Il accède à l'interface affichant :
   - Le statut d'agrément de sa ligue
   - L'Attestation d'Homologation (s'il existe)
   - Les informations officielles
   - Des conseils utiles

## Notes

- L'Attestation d'Homologation s'affiche uniquement si elle existe dans la base de données
- Le statut "Agréée" s'affiche si `attestation.statut == 'VALIDEE'`
- Le document est téléchargeable si `attestation.document_attestation` existe
- L'interface est identique à celle de la fédération pour cohérence
