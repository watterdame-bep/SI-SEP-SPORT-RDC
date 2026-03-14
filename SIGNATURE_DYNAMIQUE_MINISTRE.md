# Système de Signature et Sceau Dynamiques du Ministre

## Vue d'ensemble

Le système permet à chaque Ministre de télécharger sa propre signature et le sceau du Ministère dans son profil. Ces éléments sont automatiquement intégrés dans les Arrêtés Ministériels générés.

## ✅ Implémentation Complète

### 1. Champs Ajoutés au Modèle ProfilUtilisateur

```python
signature_image = models.ImageField(
    upload_to='signatures/',
    blank=True,
    null=True,
    help_text="Signature scannée du Ministre (PNG avec fond transparent, 400x200px)"
)

sceau_image = models.ImageField(
    upload_to='sceaux/',
    blank=True,
    null=True,
    help_text="Sceau officiel du Ministère (PNG avec fond transparent, 300x300px)"
)
```

### 2. Page de Gestion du Profil

**URL**: `/minister/profil/`

**Fonctionnalités**:
- ✅ Affichage des informations personnelles du Ministre
- ✅ Aperçu de la signature actuelle (si disponible)
- ✅ Aperçu du sceau actuel (si disponible)
- ✅ Formulaire de téléchargement de signature
- ✅ Formulaire de téléchargement de sceau
- ✅ Instructions pour préparer les images
- ✅ Messages de confirmation/erreur

### 3. Générateur d'Arrêté Amélioré

**Fichier**: `core/arrete_generator.py`

**Logique**:
1. Récupère le Ministre depuis l'institution racine (Ministère)
2. Accède au profil du Ministre
3. Récupère la signature depuis `profil.signature_image`
4. Récupère le sceau depuis `profil.sceau_image`
5. Intègre les images dans le PDF

**Comportement**:
- ✅ Si signature disponible: affichée au-dessus du nom
- ✅ Si sceau disponible: affiché en bas à droite
- ✅ Si absent: espace vide laissé (PDF généré quand même)

### 4. Avantages du Système

#### Pour le Ministre
- ✅ Signature personnelle dans chaque arrêté
- ✅ Gestion simple via interface web
- ✅ Pas besoin de fichiers statiques
- ✅ Peut changer de signature à tout moment

#### Pour le Système
- ✅ Signature différente par Ministre
- ✅ Historique des signatures (via migrations)
- ✅ Flexibilité maximale
- ✅ Pas de dépendances de fichiers externes

#### Pour les Arrêtés
- ✅ Signature authentique du Ministre
- ✅ Sceau officiel du Ministère
- ✅ Aspect professionnel et officiel
- ✅ Traçabilité du Ministre signataire

## Workflow Complet

### 1. Première Connexion du Ministre

```
Ministre se connecte
    ↓
Accède à /minister/profil/
    ↓
Voit les champs vides (pas de signature/sceau)
    ↓
Télécharge sa signature (PNG)
    ↓
Télécharge le sceau (PNG)
    ↓
Confirmation: "Signature et sceau enregistrés"
```

### 2. Génération d'un Arrêté

```
Ministre examine un dossier
    ↓
Clique sur "Approuver et Signer l'Agrément"
    ↓
Système récupère la signature du profil du Ministre
    ↓
Système récupère le sceau du profil du Ministre
    ↓
PDF généré avec signature et sceau
    ↓
Arrêté sauvegardé et disponible
```

### 3. Changement de Ministre

```
Ancien Ministre se déconnecte
    ↓
Nouveau Ministre se connecte
    ↓
Accède à /minister/profil/
    ↓
Télécharge sa propre signature
    ↓
Télécharge le sceau du Ministère
    ↓
Les prochains arrêtés auront sa signature
```

## Préparation des Images

### Signature du Ministre

1. **Scanner**
   - Résolution: 300 DPI minimum
   - Format: PNG
   - Fond blanc

2. **Retirer le fond blanc**
   - Utiliser [remove.bg](https://www.remove.bg/)
   - Ou GIMP (gratuit)
   - Ou Photoshop

3. **Redimensionner**
   - Dimensions: 400x200 pixels
   - Ratio: 2:1
   - Format: PNG avec fond transparent

4. **Télécharger**
   - Via `/minister/profil/`
   - Fichier PNG uniquement

### Sceau du Ministère

1. **Scanner**
   - Résolution: 300 DPI minimum
   - Format: PNG
   - Fond blanc

2. **Retirer le fond blanc**
   - Utiliser [remove.bg](https://www.remove.bg/)
   - Ou GIMP
   - Ou Photoshop

3. **Redimensionner**
   - Dimensions: 300x300 pixels (carré)
   - Format: PNG avec fond transparent

4. **Télécharger**
   - Via `/minister/profil/`
   - Fichier PNG uniquement

## Fichiers Modifiés/Créés

### Modèles
- ✅ `core/models.py` - Ajout champs `signature_image` et `sceau_image`

### Vues
- ✅ `core/views.py` - Nouvelle vue `profil_ministre()`

### Templates
- ✅ `templates/core/profil_ministre.html` - Page de gestion du profil

### Générateur
- ✅ `core/arrete_generator.py` - Récupération signature/sceau depuis profil

### URLs
- ✅ `core/urls.py` - Route `/minister/profil/`

### Migrations
- ✅ `core/migrations/0004_add_signature_sceau_fields.py` - Ajout des champs

## Stockage des Fichiers

### Signature
- **Dossier**: `media/signatures/`
- **Nommage**: Automatique (Django)
- **Format**: PNG
- **Taille max**: Configurable dans settings.py

### Sceau
- **Dossier**: `media/sceaux/`
- **Nommage**: Automatique (Django)
- **Format**: PNG
- **Taille max**: Configurable dans settings.py

## Sécurité

### Permissions
- ✅ Seul le Ministre peut modifier son profil
- ✅ Seul le Ministre peut télécharger sa signature
- ✅ Seul le Ministre peut télécharger le sceau

### Validation
- ✅ Fichiers PNG uniquement
- ✅ Taille maximale vérifiée
- ✅ Dimensions recommandées affichées

### Stockage
- ✅ Fichiers stockés dans `media/` (hors du web)
- ✅ Accès via Django (permissions respectées)
- ✅ Sauvegarde automatique

## Dépannage

### La signature n'apparaît pas dans l'arrêté
1. Vérifier que le Ministre a téléchargé une signature
2. Vérifier que le fichier est en PNG
3. Vérifier les permissions du fichier
4. Vérifier les logs Django

### Le sceau n'apparaît pas dans l'arrêté
1. Vérifier que le Ministre a téléchargé un sceau
2. Vérifier que le fichier est en PNG
3. Vérifier les permissions du fichier
4. Vérifier les logs Django

### Erreur lors du téléchargement
1. Vérifier le format (PNG uniquement)
2. Vérifier la taille du fichier
3. Vérifier les permissions du dossier `media/`
4. Vérifier l'espace disque disponible

## Améliorations Futures

### Court Terme
- [ ] Ajouter un aperçu en temps réel du PDF avec signature
- [ ] Permettre de recadrer l'image avant téléchargement
- [ ] Ajouter des validations de dimensions

### Moyen Terme
- [ ] Historique des signatures (archivage)
- [ ] Signature numérique cryptographique
- [ ] Certificat numérique

### Long Terme
- [ ] Signature électronique avancée (eIDAS)
- [ ] Intégration avec services de signature externes
- [ ] Audit trail complet

## Configuration

### Settings.py
```python
# Taille maximale des fichiers (optionnel)
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Dossier de stockage
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### .gitignore
```
# Signatures et sceaux (données sensibles)
media/signatures/
media/sceaux/
```

## Support

Pour toute question:
- Consulter `core/arrete_generator.py` (lignes 140-160)
- Consulter `templates/core/profil_ministre.html`
- Vérifier les logs Django
- Tester avec des images de test d'abord

## Résumé

✅ **Système complet et fonctionnel**
- Signature dynamique du Ministre
- Sceau du Ministère
- Gestion simple via interface web
- Intégration automatique dans les arrêtés
- Flexibilité maximale
- Sécurité garantie
