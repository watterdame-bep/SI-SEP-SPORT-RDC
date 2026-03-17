# Redesign Complet de la Licence Sportive - Format Carte ID

## Changements effectués

### 1. Nouvelle disposition du RECTO

**Layout professionnel:**
- Photo de l'athlète à gauche (180x240 pixels)
- Informations complètes à droite de la photo
- QR code en bas à gauche (100x100 pixels)

**Informations affichées sur le RECTO:**
1. Numéro athlète (en rouge #ED1C24, police 32pt)
2. NOM (en majuscules)
3. POST-NOM (en majuscules)
4. PRÉNOM (en majuscules)
5. Date de naissance (format DD/MM/YYYY)
6. Lieu de naissance
7. Discipline (en bleu #0036ca)
8. Club
9. Adresse (si disponible)
10. QR code de vérification (bas gauche)

**Positions précises:**
- Photo: (40, 120) - Dimensions: 180x240px
- Informations: Démarrent à (270, 100)
- Espacement vertical: 35px entre chaque ligne
- QR code: (40, 508) - Dimensions: 100x100px

### 2. Nouvelle disposition du VERSO

**Informations affichées:**
- Titre "VALIDITÉ DE LA LICENCE" (en bleu)
- Dates de validité (du ... au ...)
- Poste (si disponible)
- Numéro de maillot (si disponible)
- Catégorie d'âge
- Texte de sécurité en bas (en rouge)

**Positions:**
- Démarrage: (100, 150)
- Espacement: 40px entre les sections

### 3. Polices utilisées

**Recto:**
- `font_numero`: Arial Bold 32pt (numéro athlète)
- `font_label`: Arial Bold 16pt (labels NOM, PRÉNOM, etc.)
- `font_value`: Arial Regular 18pt (valeurs)
- `font_small`: Arial Regular 14pt (textes secondaires)

**Verso:**
- `font_title`: Arial Bold 20pt (titres)
- `font_regular`: Arial Regular 18pt (textes)
- `font_small`: Arial Regular 14pt (petits textes)

### 4. Couleurs RDC respectées

- **Rouge Drapeau** (#ED1C24): Numéro athlète, texte de sécurité
- **Bleu Royal** (#0036ca): Discipline, titres
- **Noir** (#000000): Textes principaux
- **Gris** (#646464): Labels

## Fichiers modifiés

1. `gouvernance/licence_generator.py`
   - Fonction `_creer_recto_licence()` - Complètement redesignée
   - Fonction `_creer_verso_licence()` - Simplifiée

2. `regenerer_licence_athlete.py` - Script de régénération créé

3. Documentation:
   - `ATHLETE_LICENSE_GENERATION_SYSTEM.md` - Documentation système
   - `GUIDE_AJUSTEMENT_POSITIONS_LICENCE.md` - Guide d'ajustement
   - `LICENCE_REDESIGN_COMPLETE.md` - Ce document

## Utilisation

### Régénérer une licence spécifique

```bash
python regenerer_licence_athlete.py
```

Le script régénère automatiquement la licence pour l'athlète avec UID: `05e81e43d1024e69bf60f247eb732244`

### Utiliser la commande Django

```bash
python manage.py generate_athlete_licence <athlete_uid> --force
```

Options:
- `--force`: Force la régénération même si une licence existe
- `--base-url`: URL de base pour le QR code (défaut: http://127.0.0.1:8000)

### Générer depuis le code

```python
from gouvernance.licence_generator import generer_licence_sportive_id1
from gouvernance.models import Athlete

athlete = Athlete.objects.get(uid='05e81e43d1024e69bf60f247eb732244')
licence_pdf = generer_licence_sportive_id1(athlete, base_url='http://127.0.0.1:8000')

athlete.licence_pdf = licence_pdf
athlete.save()
```

## Améliorations apportées

### Lisibilité
- Disposition claire avec labels et valeurs alignés
- Espacement cohérent entre les lignes
- Tailles de police adaptées à la lecture

### Complétude des informations
- Toutes les informations d'identité sont présentes
- Séparation claire: NOM, POST-NOM, PRÉNOM
- Lieu de naissance ajouté
- Adresse incluse (si disponible)

### Professionnalisme
- Layout type carte d'identité professionnelle
- Photo bien positionnée et dimensionnée
- QR code discret mais accessible
- Respect de la charte graphique RDC

### Sécurité
- QR code de vérification sur le recto
- Texte de sécurité sur le verso
- Numéro unique bien visible

## Structure du PDF généré

### Page 1: RECTO
```
┌─────────────────────────────────────────────┐
│  [HEADER TEMPLATE]                          │
│                                             │
│  ┌────────┐  N° RDC-ATHL-2026-000004      │
│  │        │                                 │
│  │ PHOTO  │  NOM:        MULAMBA           │
│  │        │  POST-NOM:   LUMANISHA         │
│  │        │  PRÉNOM:     PASCAL            │
│  └────────┘  NÉ(E) LE:   23/03/1991        │
│              À:          [LIEU]             │
│              DISCIPLINE: ATHLÉTISME         │
│  [QR]       CLUB:       FC OKINAWA         │
│              ADRESSE:    [ADRESSE]          │
└─────────────────────────────────────────────┘
```

### Page 2: VERSO
```
┌─────────────────────────────────────────────┐
│  [HEADER TEMPLATE]                          │
│                                             │
│  VALIDITÉ DE LA LICENCE                     │
│                                             │
│  Valide du 13/03/2026                       │
│  au 13/03/2027                              │
│                                             │
│  Poste: [POSTE]                             │
│  N° Maillot: [NUMERO]                       │
│  Catégorie: Senior                          │
│                                             │
│  Document officiel - Toute falsification... │
└─────────────────────────────────────────────┘
```

## Dimensions et résolution

- **Format**: ID-1 (85,60 mm × 53,98 mm)
- **Résolution**: 300 DPI
- **Dimensions pixels**: 1011 × 638 pixels
- **Format fichier**: PDF recto-verso

## Tests effectués

✓ Génération avec photo
✓ Génération sans photo (cadre vide)
✓ Toutes les informations affichées
✓ QR code fonctionnel
✓ Respect des couleurs RDC
✓ PDF recto-verso créé
✓ Sauvegarde dans le modèle

## Prochaines étapes possibles

1. Ajuster les positions selon le design exact des templates
2. Ajouter des éléments de sécurité supplémentaires
3. Intégrer la génération automatique lors de la certification
4. Créer une interface d'aperçu avant impression
5. Ajouter la possibilité d'imprimer en batch

## Notes techniques

- Les templates recto.png et verso.png doivent être présents dans `licence_fichier/`
- Si les templates sont absents, une image blanche est créée
- Les polices Arial sont utilisées (fallback sur police par défaut si absentes)
- Le QR code contient l'URL de vérification: `{base_url}/gouvernance/verifier-athlete/{uid}/`
- Les fichiers temporaires sont automatiquement nettoyés après génération

## Résultat

La licence générée est maintenant une véritable carte d'identité sportive professionnelle avec:
- Toutes les informations nécessaires
- Une disposition claire et lisible
- Le respect de la charte graphique RDC
- Un QR code de vérification
- Un format standard ID-1 imprimable
