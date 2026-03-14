# Templates d'Authentification - SI-SEP Sport RDC

## Structure

Tous les templates d'authentification utilisent maintenant un template de base commun : `auth_base.html`

### Template de base : `auth_base.html`

Ce template contient :
- Le panneau gauche bleu avec le logo et les informations RDC (60% sur desktop, caché sur mobile)
- Le panneau droit blanc pour le contenu (40% sur desktop, 100% sur mobile)
- Le logo RDC au-dessus du formulaire (desktop uniquement)
- Le logo du ministère (mobile uniquement)
- Tous les styles CSS communs

### Templates qui héritent de `auth_base.html`

1. **login.html** - Page de connexion
   - Formulaire avec email et mot de passe
   - Checkbox "Mémoriser cet accès"
   - Lien "Mot de passe oublié"
   - Lien "Créer un compte officiel"

2. **password_reset_form_new.html** - Demande de réinitialisation
   - Formulaire avec champ email
   - Bouton "Envoyer les instructions"
   - Lien retour vers la connexion

3. **password_reset_done_new.html** - Confirmation d'envoi
   - Message de confirmation
   - Icône de succès
   - Bouton retour vers la connexion

4. **verify_email_new.html** - Vérification email
   - Formulaire de définition du mot de passe
   - Gestion des erreurs (lien expiré/invalide)
   - Bouton d'activation

## Utilisation

### Pour créer une nouvelle page d'authentification :

```django
{% extends "core/auth_base.html" %}

{% block title %}Titre de la page | SI-SEP Sport RDC{% endblock %}

{% block content %}
<!-- Votre contenu ici -->
{% endblock %}

{% block extra_js %}
<!-- JavaScript optionnel -->
{% endblock %}

{% block extra_style %}
<!-- CSS optionnel -->
{% endblock %}
```

## Avantages

1. **Cohérence** : Toutes les pages d'authentification ont le même design
2. **Maintenabilité** : Un seul fichier à modifier pour changer le design global
3. **Responsive** : Le design s'adapte automatiquement mobile/desktop
4. **Réutilisabilité** : Facile d'ajouter de nouvelles pages d'authentification

## Fichiers

- `auth_base.html` - Template de base (NE PAS MODIFIER sans raison)
- `login.html` - Page de connexion (ACTIF)
- `login_old_backup.html` - Ancienne version (BACKUP)
- `password_reset_form_new.html` - Réinitialisation mot de passe (À ACTIVER)
- `password_reset_done_new.html` - Confirmation envoi email (À ACTIVER)
- `verify_email_new.html` - Vérification email (À ACTIVER)

## Pour activer les nouveaux templates

Remplacez les anciens fichiers par les nouveaux :
```bash
# Password reset form
Copy-Item "core/templates/core/password_reset_form_new.html" "core/templates/core/password_reset_form.html" -Force

# Password reset done
Copy-Item "core/templates/core/password_reset_done_new.html" "core/templates/core/password_reset_done.html" -Force

# Email verification
Copy-Item "core/templates/core/verify_email_new.html" "core/templates/core/verify_email.html" -Force
```
