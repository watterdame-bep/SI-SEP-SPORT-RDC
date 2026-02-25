"""
Backend d'authentification permettant la connexion par e-mail ou par nom d'utilisateur.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authentifie avec le mot de passe en acceptant soit l'e-mail soit le nom d'utilisateur.
    Si la valeur contient '@', on cherche l'utilisateur par email, sinon par username.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        username = username.strip()
        if not username:
            return None
        try:
            if "@" in username:
                user = User.objects.get(email__iexact=username)
            else:
                user = User.objects.get(username=username)
        except User.DoesNotExist:
            User().set_password(password)  # Limiter le timing des attaques
            return None
        except User.MultipleObjectsReturned:
            # Plusieurs utilisateurs avec le même email : prendre le premier
            if "@" in username:
                user = User.objects.filter(email__iexact=username).first()
            else:
                return None
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
