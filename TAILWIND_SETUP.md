# Configuration Tailwind CSS - SI-SEP Sport RDC

## Installation effectuée

Tailwind CSS a été installé et configuré pour remplacer Bootstrap, en respectant strictement la **Charte Graphique RDC Royale**.

## Couleurs de la charte

Les couleurs officielles du drapeau RDC sont définies dans `tailwind.config.js` :

- **Bleu Royal** : `#0036ca` (classe: `rdc-blue`)
- **Jaune Drapeau** : `#FDE015` (classe: `rdc-yellow`)
- **Rouge Drapeau** : `#ED1C24` (classe: `rdc-red`)

## Fichiers de configuration

- `tailwind.config.js` : Configuration Tailwind avec les couleurs RDC
- `public/assets/css/input.css` : Fichier source avec les styles personnalisés
- `public/assets/css/output.css` : Fichier CSS compilé (généré automatiquement)

## Scripts npm disponibles

### Build (production)
Compile le CSS une seule fois :
```bash
npm run build:css
```

### Watch (développement)
Compile automatiquement à chaque modification :
```bash
npm run watch:css
```

## Workflow de développement

1. **Démarrer le watch mode** (dans un terminal séparé) :
   ```bash
   npm run watch:css
   ```

2. **Lancer Django** (dans un autre terminal) :
   ```bash
   python manage.py runserver
   ```

3. Modifier vos templates HTML - Tailwind recompilera automatiquement

## Classes CSS personnalisées

### Boutons
- `.btn-primary` : Bouton bleu principal
- `.btn-warning` : Bouton jaune (à utiliser avec parcimonie)
- `.btn-danger` : Bouton rouge pour actions critiques
- `.btn-login` : Bouton de connexion avec dégradé

### Cartes
- `.card` : Carte blanche avec ombre
- `.card-header` : En-tête avec dégradé bleu

### Formulaires
- `.input-field` : Champ de formulaire avec focus bleu

### Sidebar
- `.sidebar-link-blue` : Lien de navigation
- `.active-blue` : État actif avec bordure jaune

## Règles importantes

1. **Pas de border-radius** : Tous les éléments ont des coins carrés (règle `* { border-radius: 0 !important; }`)
2. **Jaune avec parcimonie** : Utiliser uniquement pour les éléments nécessitant l'attention du Ministre
3. **Dégradés bleus** : En-têtes de cartes utilisent un dégradé du bleu royal

## Production

Avant de déployer en production, exécutez :
```bash
npm run build:css
```

Le fichier `output.css` sera minifié et optimisé.

## Suppression de Bootstrap

Bootstrap a été complètement remplacé par Tailwind CSS. Les anciens fichiers Bootstrap dans `public/assets/css/` peuvent être supprimés si nécessaire.
