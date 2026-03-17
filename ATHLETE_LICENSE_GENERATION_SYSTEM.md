# Système de Génération de Licence Sportive - Format Carte ID

## Vue d'ensemble

Le système de génération de licence sportive a été redesigné pour utiliser des templates d'images (recto.png et verso.png) sur lesquels les informations de l'athlète sont superposées, créant une véritable carte d'identité sportive au format ID-1 (85,60 mm × 53,98 mm).

## Architecture

### Fichiers modifiés
- `gouvernance/licence_generator.py` - Générateur de licence redesigné

### Templates utilisés
- `licence_fichier/recto.png` - Template pour le recto de la carte
- `licence_fichier/verso.png` - Template pour le verso de la carte

## Fonctionnement

### 1. Fonction principale: `generer_licence_sportive_id1()`

Cette fonction génère un PDF recto-verso au format ID-1 en utilisant les templates PNG.

**Processus:**
1. Charge les templates recto.png et verso.png depuis le dossier `licence_fichier/`
2. Crée l'image recto avec superposition des données
3. Crée l'image verso avec superposition des données
4. Génère un PDF avec 2 pages (recto + verso)
5. Retourne un ContentFile prêt à être sauvegardé

**Retour:**
```python
ContentFile(buffer.getvalue(), name=f"Licence_ID1_{numero_fichier}.pdf")
```

### 2. Fonction `_creer_recto_licence()`

Crée l'image recto en superposant les informations de l'athlète sur le template.

**Données superposées sur le RECTO:**
- Photo de l'athlète (200x250 pixels, position gauche)
- Numéro sportif/licence (rouge #ED1C24, police grande)
- Nom complet de l'athlète (noir, majuscules)
- Discipline sportive (bleu #0036ca)
- Club d'appartenance (gris, petit texte)
- Date de naissance

**Positions approximatives (à ajuster selon le template):**
- Photo: (50, 150)
- Numéro: (300, 80)
- Nom: (300, 140)
- Discipline: (300, 180)
- Club: (300, 220)
- Date naissance: (300, 260)

### 3. Fonction `_creer_verso_licence()`

Crée l'image verso en superposant les informations de vérification sur le template.

**Données superposées sur le VERSO:**
- QR code de vérification (150x150 pixels)
- Dates de validité de la licence
- Texte "Scanner pour vérifier"

**Positions approximatives:**
- QR code: (800, 400)
- Dates validité: (100, 450) et (100, 480)
- Texte vérification: (750, 560)

## Technologies utilisées

### Bibliothèques Python
- **PIL (Pillow)**: Manipulation d'images, superposition de texte et photos
- **ReportLab**: Génération du PDF final
- **qrcode**: Génération du QR code de vérification

### Polices
Le système tente d'utiliser les polices Arial:
- `arial.ttf` - Police régulière
- `arialbd.ttf` - Police bold

Si les polices ne sont pas disponibles, le système utilise la police par défaut de PIL.

## Couleurs RDC

Conformément à la charte graphique:
- **Bleu Royal**: RGB(0, 54, 202) - Pour la discipline
- **Rouge Drapeau**: RGB(237, 28, 36) - Pour le numéro sportif
- **Noir**: RGB(0, 0, 0) - Pour le nom et textes principaux
- **Gris**: RGB(100, 100, 100) - Pour les informations secondaires

## Format de sortie

### Dimensions
- Format: ID-1 (ISO/IEC 7810)
- Largeur: 85,60 mm
- Hauteur: 53,98 mm
- Équivalent: Format carte bancaire/permis de conduire

### Structure du PDF
- Page 1: Recto de la carte
- Page 2: Verso de la carte
- Résolution: 300 DPI pour impression de qualité

### Nom du fichier
Format: `Licence_ID1_{numero_sportif}.pdf`

Exemple: `Licence_ID1_RDC-ATHL-2026-000004.pdf`

## Utilisation

### Génération de licence

```python
from gouvernance.licence_generator import generer_licence_sportive_id1

# Générer la licence pour un athlète
licence_pdf = generer_licence_sportive_id1(athlete, base_url='http://127.0.0.1:8000')

# Sauvegarder dans le modèle
athlete.licence_pdf = licence_pdf
athlete.save()
```

### Commande de gestion

```bash
python manage.py generate_athlete_licence <athlete_uid>
```

## QR Code de vérification

Le QR code généré sur le verso contient l'URL de vérification:
```
{base_url}/gouvernance/verifier-athlete/{athlete.uid}/
```

Cette URL permet de vérifier l'authenticité de la licence en scannant le QR code.

## Gestion des erreurs

### Template manquant
Si les fichiers recto.png ou verso.png sont absents, le système crée une image blanche vide de dimensions 1011x638 pixels (équivalent ID-1 à 300 DPI).

### Photo manquante
Si l'athlète n'a pas de photo, l'espace photo reste vide (pas de placeholder sur le template).

### Polices manquantes
Si les polices Arial ne sont pas disponibles, le système utilise la police par défaut de PIL.

## Ajustements des positions

Les positions des éléments superposés sont approximatives et doivent être ajustées en fonction du design exact des templates recto.png et verso.png.

Pour ajuster les positions, modifier les coordonnées dans les fonctions:
- `_creer_recto_licence()` - Positions sur le recto
- `_creer_verso_licence()` - Positions sur le verso

## Améliorations futures

1. **Positions configurables**: Stocker les positions dans settings.py ou un fichier de configuration
2. **Polices personnalisées**: Utiliser des polices spécifiques RDC si disponibles
3. **Validation template**: Vérifier les dimensions des templates avant génération
4. **Aperçu**: Ajouter une fonction de prévisualisation avant génération finale
5. **Batch generation**: Générer plusieurs licences en une seule opération

## Notes techniques

- Les images sont converties en RGBA pour supporter la transparence
- La résolution de 300 DPI assure une qualité d'impression professionnelle
- Le PDF est généré avec ReportLab pour compatibilité maximale
- Les fichiers temporaires sont automatiquement nettoyés après génération
