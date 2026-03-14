# Système de Compétitions et Billetterie - Implémentation

## Vue d'Ensemble

Ce document décrit l'implémentation du système de gestion des compétitions provinciales et de la billetterie pour les rencontres sportives dans SI-SEP Sport RDC.

---

## Fonctionnalités Implémentées

### 1. Validation des Contraintes de Rencontres

#### Contrainte 1: Un stade ne peut pas avoir deux rencontres à la même heure
✅ **Déjà implémenté** dans `Rencontre.clean()`

#### Contrainte 2: Un club ne peut pas avoir deux rencontres le même jour
✅ **Nouvellement implémenté** dans `Rencontre.clean()`

**Fichier**: `gouvernance/models/competition.py`

```python
def clean(self):
    from django.core.exceptions import ValidationError
    errors = {}
    
    # Validation 1: Un stade ne peut pas avoir deux rencontres à la même heure
    if self.stade_id and self.date_heure:
        qs = Rencontre.objects.filter(
            stade_id=self.stade_id,
            date_heure=self.date_heure,
        )
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        if qs.exists():
            errors['date_heure'] = 'Ce stade a déjà une rencontre à cette date et heure.'
    
    # Validation 2: Un club ne peut pas avoir deux rencontres le même jour
    if self.date_heure and (self.equipe_a_id or self.equipe_b_id):
        date_match = self.date_heure.date()
        
        # Vérifier pour l'équipe A
        if self.equipe_a_id:
            qs_equipe_a = Rencontre.objects.filter(
                date_heure__date=date_match,
            ).filter(
                models.Q(equipe_a_id=self.equipe_a_id) | models.Q(equipe_b_id=self.equipe_a_id)
            )
            if self.pk:
                qs_equipe_a = qs_equipe_a.exclude(pk=self.pk)
            if qs_equipe_a.exists():
                errors['equipe_a'] = f'{self.equipe_a.nom_officiel} a déjà une rencontre programmée le {date_match.strftime("%d/%m/%Y")}.'
        
        # Vérifier pour l'équipe B
        if self.equipe_b_id:
            qs_equipe_b = Rencontre.objects.filter(
                date_heure__date=date_match,
            ).filter(
                models.Q(equipe_a_id=self.equipe_b_id) | models.Q(equipe_b_id=self.equipe_b_id)
            )
            if self.pk:
                qs_equipe_b = qs_equipe_b.exclude(pk=self.pk)
            if qs_equipe_b.exists():
                errors['equipe_b'] = f'{self.equipe_b.nom_officiel} a déjà une rencontre programmée le {date_match.strftime("%d/%m/%Y")}.'
    
    if errors:
        raise ValidationError(errors)
```

**Avantages**:
- Empêche les conflits de calendrier pour les clubs
- Vérifie à la fois l'équipe A et l'équipe B
- Messages d'erreur clairs avec le nom du club et la date

---

### 2. Vues de Gestion des Compétitions

**Fichier**: `gouvernance/views_competitions.py`

#### Vue 1: Liste des Compétitions
```python
@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_competitions_list(request):
    """Liste des compétitions organisées par la ligue."""
```

**Fonctionnalités**:
- Affiche toutes les compétitions de la ligue
- Statistiques: total, actives, saison actuelle
- Nombre de journées et rencontres par compétition

#### Vue 2: Détail d'une Compétition
```python
@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_competition_detail(request, competition_uid):
    """Détail d'une compétition avec ses journées et rencontres."""
```

**Fonctionnalités**:
- Affiche les journées de la compétition
- Liste des rencontres par journée
- Informations sur les équipes et stades

#### Vue 3: Calendrier Provincial (Drag & Drop)
```python
@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_calendrier_competition(request):
    """Interface calendrier avec drag & drop pour programmer les rencontres."""
```

**Fonctionnalités**:
- Vue calendrier interactive
- Glisser-déposer pour programmer les rencontres
- Liste des compétitions actives
- Liste des stades disponibles

**À implémenter** (Frontend):
- Intégration FullCalendar.js
- Drag & drop des rencontres
- Mise à jour AJAX

#### Vue 4: Rencontres & Billetterie
```python
@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_rencontres_billetterie(request):
    """Interface de gestion des rencontres et billetterie."""
```

**Fonctionnalités**:
- Liste des rencontres à venir
- Statut de la billetterie par rencontre
- Lien vers la configuration des tarifs

#### Vue 5: Configuration de la Billetterie
```python
@login_required
@require_role('FEDERATION_SECRETARY')
def ligue_rencontre_configurer_billetterie(request, rencontre_uid):
    """Configuration de la billetterie pour une rencontre spécifique."""
```

**Fonctionnalités**:
- Définir les tarifs par zone du stade
- Définir la capacité (nombre de billets) par zone
- Validation: capacité ≤ capacité totale du stade
- Génération automatique des billets
- Statistiques: total, vendus, utilisés, disponibles

**Actions**:
1. **Configurer les tarifs**: Définir prix et capacité par zone
2. **Générer les billets**: Créer les tickets dans la base de données

---

### 3. Routes URL

**Fichier**: `gouvernance/urls.py`

```python
# Billetterie et Rencontres
path('ligue/calendrier-provincial/', views_competitions.ligue_calendrier_competition, name='ligue_calendrier_provincial'),
path('ligue/rencontres-billetterie/', views_competitions.ligue_rencontres_billetterie, name='ligue_rencontres_billetterie'),
path('ligue/rencontres/<uuid:rencontre_uid>/billetterie/', views_competitions.ligue_rencontre_configurer_billetterie, name='ligue_rencontre_configurer_billetterie'),
```

---

## Architecture de la Billetterie

### Modèles Existants (infrastructures)

#### 1. Evenement
- Événement sportif se tenant dans une infrastructure
- Lié automatiquement à une `Rencontre` lors de sa création
- Champs: titre, type, date, heure, organisateur

#### 2. ZoneStade
- Zones du stade (Tribune d'honneur, Tribune latérale, Pourtour, etc.)
- Chaque stade peut avoir plusieurs zones
- Ordre d'affichage configurable

#### 3. EvenementZone
- **Tarif et capacité par zone pour un événement**
- Prix unitaire (CDF)
- Capacité maximale (nombre de places)
- Méthode `generer_tickets()` pour créer les billets

#### 4. Ticket
- Ticket unique avec UUID
- QR Code pour vérification anti-fraude
- Statuts: DISPONIBLE, VENDU, UTILISE, ANNULE
- Traçabilité: date d'utilisation (scan à l'entrée)

#### 5. Vente
- Vente de un ou plusieurs tickets
- Traçabilité: date, montant, canal (Guichet, Mobile Money)
- Référence de paiement
- Informations acheteur

### Workflow de Billetterie

```
1. Création Rencontre
   ↓
2. Création automatique Evenement
   ↓
3. Configuration EvenementZone (tarifs + capacités)
   ↓
4. Génération Tickets (jusqu'à capacité_max)
   ↓
5. Vente Tickets (Guichet / Mobile Money)
   ↓
6. Utilisation Tickets (Scan QR à l'entrée)
```

---

## Validations Implémentées

### Au Niveau du Modèle Rencontre

1. ✅ **Stade occupé**: Un stade ne peut pas avoir deux rencontres à la même heure
2. ✅ **Club occupé**: Un club ne peut pas avoir deux rencontres le même jour
3. ✅ **Création automatique d'événement**: Lors de la création d'une rencontre avec stade

### Au Niveau de la Configuration Billetterie

1. ✅ **Capacité du stade**: Le nombre de billets ne peut pas dépasser la capacité du stade
2. ✅ **Génération unique**: Les billets ne sont générés qu'une seule fois par zone
3. ✅ **Tarifs obligatoires**: Prix et capacité requis pour chaque zone

---

## Templates à Créer

### 1. Liste des Compétitions
**Fichier**: `templates/gouvernance/ligue_competitions_list.html`

**Contenu**:
- Tableau des compétitions avec statistiques
- Bouton "Créer une compétition"
- Liens vers détail et calendrier

### 2. Calendrier Provincial
**Fichier**: `templates/gouvernance/ligue_calendrier_competition.html`

**Contenu**:
- Calendrier interactif (FullCalendar.js)
- Drag & drop des rencontres
- Filtres par compétition
- Liste des stades disponibles

### 3. Rencontres & Billetterie
**Fichier**: `templates/gouvernance/ligue_rencontres_billetterie.html`

**Contenu**:
- Liste des rencontres à venir
- Statut billetterie (configurée / non configurée)
- Bouton "Configurer la billetterie"
- Statistiques par rencontre

### 4. Configuration Billetterie
**Fichier**: `templates/gouvernance/ligue_rencontre_configurer_billetterie.html`

**Contenu**:
- Informations de la rencontre
- Formulaire de configuration par zone:
  - Prix unitaire (CDF)
  - Capacité (nombre de billets)
- Bouton "Sauvegarder les tarifs"
- Bouton "Générer les billets"
- Statistiques de billetterie par zone

---

## Intégration avec le Menu

### Sidebar Ligue Secretary

Ajouter dans `templates/core/base.html` (section Ligue):

```html
<!-- Compétitions -->
<li>
    <a href="{% url 'gouvernance:ligue_competitions_list' %}" 
       class="flex items-center gap-3 px-4 py-2.5 text-white/80 hover:bg-white/10 rounded-lg transition-colors">
        <i class="fa-solid fa-trophy w-5"></i>
        <span>Compétitions</span>
    </a>
</li>

<!-- Calendrier Provincial -->
<li>
    <a href="{% url 'gouvernance:ligue_calendrier_provincial' %}" 
       class="flex items-center gap-3 px-4 py-2.5 text-white/80 hover:bg-white/10 rounded-lg transition-colors">
        <i class="fa-solid fa-calendar-days w-5"></i>
        <span>Calendrier Provincial</span>
    </a>
</li>

<!-- Rencontres & Billetterie -->
<li>
    <a href="{% url 'gouvernance:ligue_rencontres_billetterie' %}" 
       class="flex items-center gap-3 px-4 py-2.5 text-white/80 hover:bg-white/10 rounded-lg transition-colors">
        <i class="fa-solid fa-ticket w-5"></i>
        <span>Rencontres & Billetterie</span>
    </a>
</li>
```

---

## Prochaines Étapes

### Phase 1: Templates de Base ✅ (En cours)
- [x] Créer les vues Python
- [x] Ajouter les routes URL
- [x] Implémenter les validations
- [ ] Créer les templates HTML
- [ ] Intégrer au menu sidebar

### Phase 2: Interface Calendrier
- [ ] Intégrer FullCalendar.js
- [ ] Implémenter drag & drop
- [ ] API AJAX pour mise à jour
- [ ] Gestion des conflits en temps réel

### Phase 3: Billetterie Avancée
- [ ] Interface de vente (Guichet)
- [ ] Intégration Mobile Money
- [ ] Génération QR codes
- [ ] Scanner de tickets (entrée stade)
- [ ] Rapports de ventes

### Phase 4: Statistiques et Rapports
- [ ] Tableau de bord billetterie
- [ ] Rapports de recettes
- [ ] Analyse de fréquentation
- [ ] Export PDF/Excel

---

## Notes Techniques

### Charte Graphique RDC
- Bleu Royal: `#0036ca` (principal)
- Jaune Drapeau: `#FDE015` (accent)
- Rouge Drapeau: `#ED1C24` (danger)
- Vert: Pour succès/validation

### Bibliothèques JavaScript Recommandées
- **FullCalendar.js**: Calendrier interactif avec drag & drop
- **Chart.js**: Graphiques de statistiques
- **QRCode.js**: Génération de QR codes côté client

### Sécurité
- Validation côté serveur (Django)
- Validation côté client (JavaScript)
- Tokens CSRF pour toutes les actions
- Permissions par rôle (FEDERATION_SECRETARY)

---

## Exemples d'Utilisation

### 1. Créer une Rencontre
```python
rencontre = Rencontre.objects.create(
    journee=journee,
    equipe_a=club_a,
    equipe_b=club_b,
    stade=stade,
    date_heure=datetime(2026, 3, 20, 15, 0),  # 20/03/2026 à 15h
    statut='PROGRAMME'
)
# L'événement billetterie est créé automatiquement
```

### 2. Configurer la Billetterie
```python
# Créer les tarifs par zone
tribune_honneur = EvenementZone.objects.create(
    evenement=rencontre.evenement,
    zone_stade=zone_tribune_honneur,
    prix_unitaire=50000,  # 50 000 CDF
    devise='CDF',
    capacite_max=500  # 500 places
)

# Générer les billets
nb_generes = tribune_honneur.generer_tickets()
# Crée 500 tickets avec statut DISPONIBLE
```

### 3. Vendre un Ticket
```python
# Créer une vente
vente = Vente.objects.create(
    evenement=rencontre.evenement,
    montant_total=50000,
    devise='CDF',
    canal='GUICHET',
    acheteur_nom='Jean Dupont',
    acheteur_telephone='+243123456789'
)

# Associer un ticket à la vente
ticket = Ticket.objects.filter(
    evenement_zone=tribune_honneur,
    statut='DISPONIBLE'
).first()

ticket.vente = vente
ticket.statut = 'VENDU'
ticket.save()
```

---

## Statut Final

✅ Validation "un club ne peut pas avoir deux rencontres le même jour"
✅ Validation "un stade ne peut pas avoir deux rencontres à la même heure"
✅ Vues Python pour gestion compétitions et billetterie
✅ Routes URL configurées
✅ Architecture billetterie documentée

🔄 À faire:
- Templates HTML
- Interface calendrier drag & drop
- Intégration au menu sidebar
- Tests et validation

---

## Commandes Utiles

```bash
# Créer les migrations si nécessaire
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Créer des zones de stade pour un stade
python manage.py shell
>>> from infrastructures.models import Infrastructure, ZoneStade
>>> stade = Infrastructure.objects.get(nom="Stade des Martyrs")
>>> ZoneStade.objects.create(infrastructure=stade, nom="Tribune d'honneur", ordre=1)
>>> ZoneStade.objects.create(infrastructure=stade, nom="Tribune latérale", ordre=2)
>>> ZoneStade.objects.create(infrastructure=stade, nom="Pourtour", ordre=3)
```
