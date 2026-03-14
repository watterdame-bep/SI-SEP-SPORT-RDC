# Configuration de la Signature et du Sceau Ministériel

## Vue d'ensemble

Le système d'Arrêté Ministériel peut intégrer automatiquement:
1. La signature scannée du Ministre
2. Le sceau officiel du Ministère des Sports et Loisirs

Ces éléments sont ajoutés automatiquement lors de la génération du PDF de l'arrêté.

## Fichiers Requis

### 1. Signature du Ministre
- **Nom du fichier**: `signature-ministre.png`
- **Emplacement**: `public/assets/images/signature-ministre.png`
- **Format**: PNG avec fond transparent
- **Dimensions recommandées**: 400x200 pixels (ratio 2:1)
- **Résolution**: 300 DPI minimum pour une qualité professionnelle

### 2. Sceau du Ministère
- **Nom du fichier**: `sceau-ministere.png`
- **Emplacement**: `public/assets/images/sceau-ministere.png`
- **Format**: PNG avec fond transparent
- **Dimensions recommandées**: 300x300 pixels (carré)
- **Résolution**: 300 DPI minimum

## Instructions d'Installation

### Étape 1: Préparer les Images

1. **Scanner la signature du Ministre**
   - Scanner à 300 DPI minimum
   - Format PNG
   - Retirer le fond blanc (utiliser un outil comme Photoshop, GIMP, ou remove.bg)
   - Recadrer pour ne garder que la signature
   - Redimensionner à 400x200 pixels

2. **Scanner le sceau du Ministère**
   - Scanner à 300 DPI minimum
   - Format PNG
   - Retirer le fond blanc si nécessaire
   - Recadrer en carré
   - Redimensionner à 300x300 pixels

### Étape 2: Placer les Fichiers

```bash
# Copier les fichiers dans le bon répertoire
cp signature-ministre.png public/assets/images/
cp sceau-ministere.png public/assets/images/
```

### Étape 3: Vérifier l'Installation

Les fichiers doivent être accessibles aux URLs suivantes:
- `http://localhost:8000/static/assets/images/signature-ministre.png`
- `http://localhost:8000/static/assets/images/sceau-ministere.png`

## Comportement du Système

### Si les fichiers sont présents
- ✅ La signature du Ministre apparaît au-dessus de son nom
- ✅ Le sceau du Ministère apparaît en bas à droite
- ✅ Le PDF a un aspect officiel et professionnel

### Si les fichiers sont absents
- ⚠️ Le système génère quand même le PDF
- ⚠️ Un espace vide est laissé pour la signature
- ⚠️ Le nom du Ministre apparaît sans signature visuelle
- ⚠️ Pas de sceau visible

## Sécurité

### Protection des Fichiers
Les fichiers de signature et sceau sont des éléments sensibles. Assurez-vous de:

1. **Limiter l'accès en écriture**
   ```bash
   # Linux/Mac
   chmod 644 public/assets/images/signature-ministre.png
   chmod 644 public/assets/images/sceau-ministere.png
   ```

2. **Ne pas versionner dans Git** (déjà configuré dans .gitignore)
   ```
   # .gitignore
   public/assets/images/signature-ministre.png
   public/assets/images/sceau-ministere.png
   ```

3. **Sauvegarder dans un endroit sécurisé**
   - Garder une copie des originaux hors du serveur
   - Utiliser un coffre-fort numérique

## Alternative: Signature Dynamique depuis le Profil

### Option Future (à implémenter)

Au lieu de fichiers statiques, on peut stocker la signature dans le profil du Ministre:

1. **Ajouter un champ au modèle ProfilUtilisateur**
   ```python
   signature_image = models.ImageField(
       upload_to='signatures/',
       blank=True,
       null=True,
       help_text="Signature scannée du Ministre"
   )
   ```

2. **Modifier le générateur d'arrêté**
   ```python
   # Récupérer la signature depuis le profil
   if ministre_membre and ministre_membre.personne.profil_sisep:
       if ministre_membre.personne.profil_sisep.signature_image:
           signature_path = ministre_membre.personne.profil_sisep.signature_image.path
   ```

3. **Avantages**
   - Signature différente par Ministre
   - Gestion via l'interface admin
   - Historique des signatures
   - Plus flexible

## Outils Recommandés

### Pour Retirer le Fond Blanc
- **En ligne**: [remove.bg](https://www.remove.bg/)
- **Logiciel gratuit**: [GIMP](https://www.gimp.org/)
- **Logiciel payant**: Adobe Photoshop

### Pour Scanner
- Scanner physique à 300 DPI minimum
- Application mobile: Adobe Scan, CamScanner
- Appareil photo haute résolution (12MP+)

## Exemple de Résultat

### Avec Signature et Sceau
```
Fait à Kinshasa, le 27/02/2026

[IMAGE: Signature manuscrite]

Hon. Jean KABONGO TSHILOMBO
Ministre des Sports et Loisirs

[IMAGE: Sceau circulaire du Ministère]
```

### Sans Signature ni Sceau
```
Fait à Kinshasa, le 27/02/2026


Hon. Jean KABONGO TSHILOMBO
Ministre des Sports et Loisirs

```

## Dépannage

### La signature n'apparaît pas
1. Vérifier que le fichier existe: `public/assets/images/signature-ministre.png`
2. Vérifier les permissions du fichier (lecture autorisée)
3. Vérifier le format (PNG uniquement)
4. Vérifier les logs Django pour les erreurs

### Le sceau n'apparaît pas
1. Vérifier que le fichier existe: `public/assets/images/sceau-ministere.png`
2. Vérifier les permissions du fichier
3. Vérifier le format (PNG uniquement)

### La qualité est mauvaise
1. Augmenter la résolution du scan (300 DPI minimum)
2. Utiliser un format PNG (pas JPG)
3. Vérifier les dimensions recommandées

## Support

Pour toute question:
- Consulter `core/arrete_generator.py` (lignes de gestion des images)
- Vérifier les logs Django
- Tester avec des images de test d'abord
