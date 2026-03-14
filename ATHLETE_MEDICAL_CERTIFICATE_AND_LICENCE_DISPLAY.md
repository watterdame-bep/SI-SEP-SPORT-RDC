# Affichage du Certificat Médical et Génération de Licence - Implémentation Complète

## Résumé de la Session

Cette session a porté sur deux tâches principales :
1. Affichage du certificat médical (F72) dans l'interface de validation de la ligue
2. Génération manuelle de la licence PDF pour les athlètes certifiés nationalement

---

## TÂCHE 1 : Affichage du Certificat Médical (F72)

### Problème Initial
Le secrétaire de la ligue ne pouvait pas voir le certificat médical (F72) généré automatiquement par le médecin lors de la validation de l'athlète.

### Solution Implémentée

#### 1. Modification du Template de Validation
**Fichier**: `templates/gouvernance/ligue_athlete_validate.html`

Ajout d'une section pour afficher et télécharger le certificat médical après les recommandations de sécurité :

```html
<!-- Certificat d'Aptitude (F72) -->
{% if visite_certification.certificat_aptitude_joint or athlete.certificat_medical_enrolement %}
<div class="pt-4 border-t border-slate-200">
    <div class="bg-green-50 rounded-lg p-4 border-2 border-green-200">
        <div class="flex items-start gap-3">
            <div class="flex-shrink-0">
                <div class="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
                    <i class="fa-solid fa-file-medical text-green-600 text-lg"></i>
                </div>
            </div>
            <div class="flex-1">
                <p class="text-xs font-bold text-green-800 uppercase mb-1 flex items-center gap-1">
                    <i class="fa-solid fa-check-circle"></i> Certificat d'Aptitude (F72)
                </p>
                <p class="text-sm text-green-700 mb-3">
                    Le certificat médical d'aptitude a été généré automatiquement par le système après validation de l'examen médical.
                </p>
                {% if visite_certification.certificat_aptitude_joint %}
                <a href="{{ visite_certification.certificat_aptitude_joint.url }}" target="_blank" class="inline-flex items-center gap-2 px-4 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-semibold text-sm shadow-sm">
                    <i class="fa-solid fa-download"></i>
                    Télécharger le Certificat F72
                </a>
                {% elif athlete.certificat_medical_enrolement %}
                <a href="{{ athlete.certificat_medical_enrolement.url }}" target="_blank" class="inline-flex items-center gap-2 px-4 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-semibold text-sm shadow-sm">
                    <i class="fa-solid fa-download"></i>
                    Télécharger le Certificat F72
                </a>
                {% endif %}
            </div>
        </div>
    </div>
</div>
{% endif %}
```

### Caractéristiques
- Affichage conditionnel : le certificat n'apparaît que s'il existe
- Deux sources possibles : `visite_certification.certificat_aptitude_joint` ou `athlete.certificat_medical_enrolement`
- Design cohérent avec la charte graphique RDC (vert pour validation médicale)
- Bouton de téléchargement avec icône Font Awesome
- Ouverture dans un nouvel onglet

---

## TÂCHE 2 : Génération Manuelle de Licence PDF

### Problème Initial
Après avoir désactivé la génération automatique de licence PDF lors de la certification nationale, les athlètes certifiés n'avaient pas de licence PDF disponible dans la galerie de licences du club.

### Solution Implémentée

#### 1. Commande de Régénération du Certificat Médical
**Fichier**: `gouvernance/management/commands/regenerate_athlete_certificate.py`

Commande Django pour régénérer le certificat médical (F72) d'un athlète :

```bash
python manage.py regenerate_athlete_certificate "Nom de l'athlète"
```

**Fonctionnalités** :
- Recherche de l'athlète par nom
- Affichage des informations de l'athlète et de la visite médicale
- Régénération du PDF du certificat F72
- Sauvegarde dans `visite.certificat_aptitude_joint` et `athlete.certificat_medical_enrolement`

#### 2. Commande de Génération de Licence
**Fichier**: `gouvernance/management/commands/generate_athlete_licence.py`

Commande Django pour générer la licence PDF d'un athlète certifié national :

```bash
python manage.py generate_athlete_licence "Nom de l'athlète"
```

**Fonctionnalités** :
- Recherche de l'athlète par nom
- Vérification du statut de certification (doit être CERTIFIE_NATIONAL)
- Vérification des informations de licence (numéro, dates)
- Génération du PDF de licence (format A4 ou ID-1)
- Sauvegarde dans `athlete.licence_pdf`

**Validations** :
- L'athlète doit être certifié national
- Le numéro de licence doit exister
- La date d'émission doit être renseignée

#### 3. Correction de l'Import
La fonction dans `licence_generator.py` s'appelle `generer_licence_sportive` et non `generer_licence_pdf`.

### Résultats
- Certificat médical régénéré avec succès pour "Mulamba Lumanisha Pascal"
- Licence PDF générée avec succès au format ID-1
- Fichier sauvegardé : `licences/Licence_ID1_RDC-ATHL-2026-000004_FLFtArU.pdf`

---

## Workflow Complet de Certification

### 1. Enregistrement par le Club
- Le secrétaire du club enregistre l'athlète (statut: PROVISOIRE)

### 2. Transfert au Médecin
- Le secrétaire de la ligue transfère l'athlète au médecin (statut: EN_ATTENTE_EXAMEN_MEDICAL)

### 3. Examen Médical
- Le médecin effectue l'examen médical (F67)
- Le système génère automatiquement le certificat d'aptitude (F72)
- Statut: EN_ATTENTE_VALIDATION_LIGUE

### 4. Validation Provinciale
- Le secrétaire de la ligue valide l'athlète
- **NOUVEAU** : Le certificat F72 est visible et téléchargeable
- Statut: CERTIFIE_PROVINCIAL

### 5. Certification Nationale
- Le secrétaire de la fédération certifie l'athlète
- Les informations de licence sont enregistrées (numéro, dates)
- **PAS de génération automatique de PDF** (désactivé)
- Statut: CERTIFIE_NATIONAL

### 6. Génération Manuelle de Licence
- Utiliser la commande : `python manage.py generate_athlete_licence "Nom Athlète"`
- Le PDF est généré et sauvegardé
- La licence apparaît dans la galerie du club

---

## Fichiers Modifiés

### Templates
- `templates/gouvernance/ligue_athlete_validate.html` - Ajout section certificat F72

### Commandes Django
- `gouvernance/management/commands/regenerate_athlete_certificate.py` - Nouvelle commande
- `gouvernance/management/commands/generate_athlete_licence.py` - Nouvelle commande

### Générateurs (Référence)
- `gouvernance/certificat_aptitude_generator.py` - Génération F72
- `gouvernance/licence_generator.py` - Génération licence (formats A4 et ID-1)

---

## Prochaines Étapes (Compétitions & Billetterie)

### Fonctionnalités à Implémenter

#### 1. Validation des Contraintes
- **Un club ne peut pas avoir deux rencontres le même jour**
  - Ajouter validation dans `Rencontre.clean()`
  - Vérifier les rencontres existantes pour equipe_a et equipe_b

- **Un stade ne peut pas avoir deux rencontres à la même heure**
  - ✓ Déjà implémenté dans `Rencontre.clean()`

#### 2. Menu Calendrier Provincial
- Créer une vue pour afficher le calendrier avec drag & drop
- Interface de glisser-déposer pour programmer les rencontres
- Utiliser FullCalendar.js ou une bibliothèque similaire

#### 3. Interface Rencontres & Billetterie
- Permettre au gestionnaire de définir les tarifs des billets
- Renseigner le nombre de billets à générer par catégorie
- Validation : nombre de billets ≤ capacité du stade
- Lien avec le modèle `Evenement` (infrastructures)

### Modèles Existants
- ✓ `TypeCompetition` - Types de compétition par ligue
- ✓ `Competition` - Compétitions par saison
- ✓ `Journee` - Journées/phases d'une compétition
- ✓ `Rencontre` - Matchs avec validation stade/heure
- ✓ `CalendrierCompetition` - Dates du calendrier
- ✓ Lien automatique avec `Evenement` (billetterie)

### Modèles à Vérifier/Compléter
- `infrastructures.Evenement` - Événements billetterie
- Modèle de tarification des billets
- Modèle de génération des billets

---

## Notes Techniques

### Charte Graphique RDC
- Bleu Royal : `#0036ca` (principal)
- Jaune Drapeau : `#FDE015` (accent)
- Rouge Drapeau : `#ED1C24` (danger)
- Vert : Pour validation médicale/succès

### Formats de Licence
- **Format A4** : `generer_licence_sportive()` - Document complet
- **Format ID-1** : `generer_licence_sportive_id1()` - Carte (85,60 mm × 53,98 mm)

### Commandes Utiles
```bash
# Régénérer certificat médical
python manage.py regenerate_athlete_certificate "Nom Athlète"

# Générer licence PDF
python manage.py generate_athlete_licence "Nom Athlète"
```

---

## Statut Final

✅ Affichage du certificat médical (F72) dans l'interface de validation
✅ Commande de régénération du certificat médical
✅ Commande de génération de licence PDF
✅ Test réussi pour l'athlète "Mulamba Lumanisha Pascal"

🔄 À faire : Système de compétitions et billetterie (contraintes, calendrier, tarification)
