"""
Crée le compte Administrateur développeur (Super Admin système).
Usage : python manage.py create_dev_admin --email votre@email.com [--password MOT_DE_PASSE]
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import ProfilUtilisateur, RoleUtilisateur

User = get_user_model()


class Command(BaseCommand):
    help = "Crée le superutilisateur Administrateur développeur (accès setup SI-SEP)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='Adresse e-mail de l\'administrateur développeur',
        )
        parser.add_argument(
            '--password',
            type=str,
            default=None,
            help='Mot de passe (sinon demandé en interactif ou variable DEV_ADMIN_PASSWORD)',
        )

    def handle(self, *args, **options):
        email = options['email'].strip().lower()
        if not email or '@' not in email:
            self.stderr.write(self.style.ERROR('Indiquez une adresse e-mail valide (--email).'))
            return
        password = options.get('password') or os.environ.get('DEV_ADMIN_PASSWORD')
        if not password:
            from getpass import getpass
            password = getpass('Mot de passe administrateur développeur: ')
            if not password:
                self.stderr.write(self.style.ERROR('Mot de passe requis.'))
                return
        username = email  # Connexion par e-mail, username = email pour simplicité
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            user.set_password(password)
            user.email = email
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.save()
            self.stdout.write(self.style.WARNING(f'Utilisateur existant mis à jour : {email}'))
        else:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
            )
            self.stdout.write(self.style.SUCCESS(f'Superutilisateur créé : {email}'))
        profil, created = ProfilUtilisateur.objects.get_or_create(
            user=user,
            defaults={
                'role': RoleUtilisateur.SYSTEM_SUPER_ADMIN,
                'actif': True,
            },
        )
        if not created:
            profil.role = RoleUtilisateur.SYSTEM_SUPER_ADMIN
            profil.actif = True
            profil.save()
            self.stdout.write(self.style.WARNING('Profil Super Admin déjà présent, mis à jour.'))
        else:
            self.stdout.write(self.style.SUCCESS('Profil Administrateur développeur (SYSTEM_SUPER_ADMIN) créé.'))
        self.stdout.write('Connexion : /login/ avec votre e-mail et ce mot de passe.')
