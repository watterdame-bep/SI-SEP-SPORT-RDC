# Implémentation de la Génération de Licence avec Template HTML

## Vue d'ensemble

La génération de licence sportive utilise maintenant le template HTML `essai.html` du dossier `licence_fichier/` pour créer des cartes professionnelles au format ID-1 avec une disposition optimale.

## Architecture

### Fichiers créés/modifiés

1. **gouvernance/licence_generator_html.py** - Nouveau générateur utilisant xhtml2pdf
2. **licence_fichier/essai.html** - Template HTML amélioré
3. **regenerer_licence_athlete.py** - Script de régénération mis à jour

### Bibliothèques utilisées

- **xhtml2pdf**: Conversion HTML vers PDF (plus simple que weasyprint sur Windows)
- **qrcode**: Génération du QR code de vérification
- **Pillow**: Manipulation d'images

## Template HTML (essai.html)

### Structure

Le template définit deux cartes (recto et verso) au format ID-1 (85,6mm × 53,98mm):

**RECTO:**
- Photo de l'athlète (18mm × 22mm) à gauche
- Numéro athlète en haut (rouge #ED1C24)
- Informations d'identité:
  - NOM
  - POST-NOM
  - PRÉNOM
  - NÉ(E) LE
  - DISCIPLINE (bleu #0056b3)
- QR code en bas à gauche (10mm × 10mm)

**VERSO:**
- PROVINCE
- LIEU DE NAISSANCE
- CLUB
- GROUPE SANGUIN (rouge)
- Texte de sécurité en bas

### Styles CSS

```css
.card-container {
    width: 85.6mm;
    height: 53.98mm;
    border-radius: 3mm;
    background-size: cover;
}

.athlete-photo {
    position: absolute;
    top: 18mm;
    left: 5mm;
    width: 18mm;
    height: 22mm;
    border: 0.5mm solid #0056b3;
}

.qr-code {
    position: absolute;
    bottom: 4mm;
    left: 5mm;  /* En bas à gauche comme demandé */
    width: 10mm;
    height: 10mm;
}
```

## Fonction principale

### `generer_licence_sportive_id1(athlete, base_url=None)`

**Processus:**
1. Génère le QR code de vérification
2. Charge le template HTML
3. Remplace les variables par les données de l'athlète
4. Convertit le HTML en PDF avec xhtml2pdf
5. Retourne un ContentFile prêt à sauvegarder

**Paramètres:**
- `athlete`: Instance du modèle Athlete
- `base_url`: URL de base pour le QR code (optionnel)

**Retour:**
```python
ContentFile(pdf_buffer.getvalue(), name=f"Licence_ID1_{numero_fichier}.pdf")
```

## Remplacement des variables

### Fonction `_remplacer_variables_template()`

Remplace les variables Django template par les vraies valeurs:

```python
replacements = {
    '{{ athlete.photo.url }}': photo_path,
    '{{ athlete.nom }}': nom.upper(),
    '{{ athlete.postnom }}': postnom.upper(),
    '{{ athlete.prenom }}': prenom.upper(),
    '{{ athlete.id_sportif }}': numero_sportif,
    '{{ athlete.discipline.nom }}': discipline,
    '{{ athlete.qr_code.url }}': qr_path,
    '{{ athlete.province.nom }}': province,
    '{{ athlete.date_naissance|date:"d/m/Y" }}': date_naissance,
    '{{ athlete.visite_medicale.groupe_sanguin }}': groupe_sanguin,
    '{{ athlete.lieu_naissance }}': lieu_naissance,
    '{{ athlete.club }}': club,
}
```

## Avantages de cette approche

### 1. Facilité de modification
- Modifier la disposition = éditer le HTML/CSS
- Pas besoin de recompiler ou modifier le code Python
- Prévisualisation possible dans un navigateur

### 2. Meilleure qualité
- Rendu professionnel avec CSS
- Gestion automatique des polices et espacements
- Support natif des images de fond (recto.png, verso.png)

### 3. Performance
- Fichiers PDF plus légers (179KB vs 5MB)
- Génération plus rapide
- Moins de dépendances système

### 4. Maintenabilité
- Séparation claire entre présentation (HTML) et logique (Python)
- Facile à tester et déboguer
- Réutilisable pour d'autres types de cartes

## Utilisation

### Régénérer une licence

```bash
python regenerer_licence_athlete.py
```

### Depuis le code

```python
from gouvernance.licence_generator_html import generer_licence_sportive_id1

licence_pdf = generer_licence_sportive_id1(athlete, base_url='http://127.0.0.1:8000')
athlete.licence_pdf = licence_pdf
athlete.save()
```

### Commande Django

```bash
python manage.py generate_athlete_licence <athlete_uid> --force
```

## Personnalisation du template

### Modifier les positions

Éditer `licence_fichier/essai.html`:

```css
.athlete-photo {
    top: 18mm;    /* Ajuster la position verticale */
    left: 5mm;    /* Ajuster la position horizontale */
    width: 18mm;  /* Ajuster la largeur */
    height: 22mm; /* Ajuster la hauteur */
}
```

### Modifier les couleurs

```css
.info-label {
    color: #0056b3;  /* Bleu pour les labels */
}

.numero-athlete {
    color: #ED1C24;  /* Rouge RDC pour le numéro */
}
```

### Ajouter des champs

1. Ajouter dans le HTML:
```html
<div class="info-label">NOUVEAU CHAMP</div>
<div class="info-value">{{ athlete.nouveau_champ }}</div>
```

2. Ajouter dans `_remplacer_variables_template()`:
```python
replacements['{{ athlete.nouveau_champ }}'] = athlete.nouveau_champ
```

## Images de fond

Le template utilise les images `recto.png` et `verso.png` comme fond:

```css
.recto {
    background-image: url('recto.png');
}

.verso {
    background-image: url('verso.png');
}
```

Ces images doivent être présentes dans `licence_fichier/` et contenir:
- En-têtes officiels
- Logos RDC
- Éléments de sécurité
- Design de la carte

## QR Code

### Position
Le QR code est maintenant en bas à gauche comme demandé:

```css
.qr-code {
    position: absolute;
    bottom: 4mm;
    left: 5mm;  /* Bas gauche */
    width: 10mm;
    height: 10mm;
}
```

### Contenu
Le QR code contient l'URL de vérification:
```
{base_url}/gouvernance/verifier-athlete/{athlete.uid}/
```

## Informations affichées

### Recto
1. Photo de l'athlète
2. Numéro athlète (N° RDC-ATHL-2026-000004)
3. NOM (en majuscules)
4. POST-NOM (en majuscules)
5. PRÉNOM (en majuscules)
6. Date de naissance (format DD/MM/YYYY)
7. Discipline
8. QR code de vérification

### Verso
1. Province d'origine
2. Lieu de naissance
3. Club
4. Groupe sanguin
5. Texte de sécurité

## Résultat

### Taille du fichier
- Ancien système (PIL): ~5MB
- Nouveau système (HTML): ~179KB
- Réduction: 96%

### Qualité
- Rendu professionnel
- Texte net et lisible
- Images bien intégrées
- Respect du format ID-1

### Compatibilité
- Fonctionne sur Windows sans dépendances système complexes
- Compatible avec tous les lecteurs PDF
- Imprimable directement

## Dépannage

### Le PDF est vide
- Vérifier que `essai.html` existe dans `licence_fichier/`
- Vérifier les chemins des images (photo, QR code, fond)

### Les images ne s'affichent pas
- Utiliser des chemins absolus pour les images
- Vérifier que les fichiers existent

### Le CSS n'est pas appliqué
- xhtml2pdf supporte un sous-ensemble de CSS
- Éviter les propriétés CSS3 avancées
- Utiliser des unités absolues (mm, px)

### Erreur de génération
- Vérifier que xhtml2pdf est installé: `pip install xhtml2pdf`
- Vérifier les permissions d'écriture dans `media/licences/`

## Prochaines étapes

1. Finaliser le design des images recto.png et verso.png
2. Ajuster les positions selon le design final
3. Ajouter des éléments de sécurité supplémentaires
4. Intégrer la génération automatique lors de la certification
5. Créer une interface de prévisualisation

## Notes techniques

- xhtml2pdf utilise ReportLab en arrière-plan
- Les polices système sont utilisées automatiquement
- Le format ID-1 est respecté (85,6mm × 53,98mm)
- Les fichiers temporaires sont automatiquement nettoyés
- Le QR code est généré à chaque fois pour garantir l'unicité
