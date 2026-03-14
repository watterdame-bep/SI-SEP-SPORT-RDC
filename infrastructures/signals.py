"""
Signaux pour le module Infrastructures.
Envoie des emails au gestionnaire quand une infrastructure est validée par le SG.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Infrastructure


@receiver(post_save, sender=Infrastructure)
def infrastructure_validation_signal(sender, instance, created, **kwargs):
    """
    Signal déclenché quand une infrastructure est validée.
    L'email est envoyé par la vue de validation du SG, pas ici.
    """
    # Le signal n'envoie pas d'email à la création
    # L'email est envoyé uniquement quand le SG valide l'infrastructure
    # via la fonction send_infrastructure_manager_activation_email dans views_sg_validation.py
    pass
