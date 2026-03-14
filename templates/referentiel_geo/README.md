# Interface Paramètres Géographiques

## Architecture Hybride : Onglets + Drill-down

Cette interface permet au Secrétaire Général de gérer le référentiel territorial de la RDC.

### Structure hiérarchique

```
Province Administrative (ProvAdmin)
  └── Territoire/Ville (TerritoireVille)
      └── Secteur/Commune (SecteurCommune)
          └── Groupement/Quartier (GroupementQuartier)
```

### Fonctionnalités

1. **Navigation par onglets** : 4 onglets pour chaque niveau géographique
2. **Drill-down hiérarchique** : Cliquer sur un élément pour voir ses enfants
3. **Breadcrumb** : Navigation contextuelle pour remonter dans la hiérarchie
4. **Statistiques globales** : Compteurs en temps réel dans le header
5. **CRUD complet** : Créer, modifier, supprimer pour chaque niveau

### URLs

- Page principale : `/parametres-geographiques/`
- API Provinces : `/parametres-geographiques/api/provinces/`
- API Territoires : `/parametres-geographiques/api/territoires/<province_id>/`
- API Secteurs : `/parametres-geographiques/api/secteurs/<territoire_id>/`
- API Groupements : `/parametres-geographiques/api/groupements/<secteur_id>/`

### Permissions

Réservé au Secrétaire Général uniquement (`est_secretaire_general_ministere`)

### Technologies

- Django templates + AJAX
- Tailwind CSS
- Font Awesome icons
- Charte graphique RDC (Bleu #0036ca, Jaune #FDE015, Rouge #ED1C24)
