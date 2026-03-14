# Redimensionnement Automatique de la Signature et du Sceau

## Résumé des modifications

Le système génère maintenant automatiquement les arrêtés ministériels avec redimensionnement intelligent de la signature et du sceau du Ministre, même si les fichiers uploadés sont plus grands que les dimensions recommandées.

## Fonctionnalités

### 1. Redimensionnement Automatique
- **Signature**: Redimensionnée automatiquement à max 4cm × 2cm
- **Sceau**: Redimensionné automatiquement à max 3cm × 3cm
- **Préservation du ratio d'aspect**: Les images ne sont jamais déformées
- **Transparence préservée**: Les images PNG avec fond transparent restent transparentes

### 2. Processus Technique

#### Fonction `redimensionner_image()`
```python
def redimensionner_image(image_path, max_width_cm, max_height_cm):
    """
    Redimensionne une image pour qu'elle ne dépasse pas les dimensions max.
    Préserve le ratio d'aspect.
    Retourne un BytesIO avec l'image redimensionnée en PNG.
    """
```

**Étapes**:
1. Ouvre l'image depuis le chemin du fichier
2. Convertit en RGBA si nécessaire (préserve la transparence)
3. Convertit les dimensions cm en pixels (1 cm ≈ 37.8 pixels à 96 DPI)
4. Calcule le ratio d'aspect pour ne pas dépasser les limites
5. Redimensionne avec interpolation LANCZOS (haute qualité)
6. Retourne l'image en BytesIO (prête pour ReportLab)

#### Intégration dans le PDF
```python
# Signature du Ministre - redimensionnée automatiquement
if ministre_profil and ministre_profil.signature_image:
    signature_buffer = redimensionner_image(ministre_profil.signature_image.path, 4, 2)
    if signature_buffer:
        signature_img = Image(signature_buffer, width=4*cm, height=2*cm)
        signature_img.hAlign = 'RIGHT'
        story.append(signature_img)

# Sceau du Ministère - redimensionné automatiquement
if ministre_profil and ministre_profil.sceau_image:
    sceau_buffer = redimensionner_image(ministre_profil.sceau_image.path, 3, 3)
    if sceau_buffer:
        sceau_img = Image(sceau_buffer, width=3*cm, height=3*cm)
        sceau_img.hAlign = 'RIGHT'
        story.append(sceau_img)
```

## Avantages

✅ **Pas de débordement**: La signature et le sceau ne dépassent jamais les limites du PDF
✅ **Flexibilité**: L'utilisateur peut uploader des images de n'importe quelle taille
✅ **Qualité**: Utilise LANCZOS pour une meilleure qualité de redimensionnement
✅ **Transparence**: Préserve les fonds transparents des PNG
✅ **Gestion d'erreurs**: Si le redimensionnement échoue, le PDF est généré sans l'image

## Fichiers modifiés

- `core/arrete_generator.py`: Ajout de la fonction `redimensionner_image()` et modification de `generer_arrete_agrement()`

## Dépendances

- **Pillow** (>=10.0.0): Déjà présent dans `requirements.txt`
- **ReportLab** (>=4.0.0): Déjà présent dans `requirements.txt`

## Recommandations pour l'utilisateur

Bien que le système redimensionne automatiquement, il est recommandé de respecter les dimensions suggérées pour une meilleure qualité:

- **Signature**: 400×200 pixels (PNG, fond transparent)
- **Sceau**: 300×300 pixels (PNG, fond transparent)

## Flux de travail

1. Ministre accède à `/minister/profil/`
2. Upload sa signature (PNG, n'importe quelle taille)
3. Upload le sceau du ministère (PNG, n'importe quelle taille)
4. Lors de la signature d'un arrêté, les images sont automatiquement redimensionnées
5. Le PDF généré contient les images redimensionnées sans débordement

