# Configuration SMTP Gmail - Guide Rapide

## Configuration Appliquée ✅

**Fichier** : `config/settings.py`

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'dev.jconsult@gmail.com'
EMAIL_HOST_PASSWORD = 'ndlfauwjttiabfim'
DEFAULT_FROM_EMAIL = 'SI-SEP Sport <dev.jconsult@gmail.com>'
```

## Paramètres

| Paramètre | Valeur |
|-----------|--------|
| Serveur | smtp.gmail.com |
| Port | 587 |
| Protocole | TLS |
| Email | dev.jconsult@gmail.com |
| Mot de passe | ndlfauwjttiabfim |

## Fonctionnalités Activées

✅ Vérification d'email lors de la création de compte
✅ Notification d'agrément de fédération avec documents
✅ Autres communications système

## Test Rapide

```bash
python manage.py shell -c "
from django.core.mail import send_mail
send_mail(
    'Test SI-SEP',
    'Email de test',
    'dev.jconsult@gmail.com',
    ['votre-email@example.com'],
    fail_silently=False,
)
"
```

## Dépannage

### Email non envoyé
- Vérifier les logs : `tail -f logs/sisep.log`
- Vérifier la connexion Internet
- Vérifier que le compte Gmail n'est pas bloqué

### Erreur d'authentification
- Vérifier le mot de passe
- Vérifier que 2FA est activé sur Gmail
- Générer un mot de passe d'application

### Erreur de connexion
- Vérifier le port (587)
- Vérifier les règles firewall
- Tester : `telnet smtp.gmail.com 587`

## Sécurité

⚠️ **Important** : 
- Ne pas commiter le mot de passe dans Git
- Utiliser des variables d'environnement en production
- Considérer un mot de passe d'application Gmail

## Prochaines Étapes

1. Tester l'envoi d'email
2. Créer une fédération pour tester l'email d'agrément
3. Vérifier la réception des emails
4. En production, utiliser un service d'email professionnel

## Statut

✅ Configuration SMTP Gmail activée
✅ Prêt pour envoyer des emails réels
