# -*- coding: utf-8 -*-
"""
Médecin de la Ligue Provinciale : enregistrement en tant qu'agent, séparé de la création de compte.
La Ligue (ou la Division) enregistre le médecin ; la Division crée éventuellement un compte pour lui.
"""
import uuid
from django.db import models


class MedecinLigue(models.Model):
    """
    Médecin désigné pour une ligue provinciale (enregistré comme Agent).
    L'enregistrement (agent + numéro Ordre des Médecins) est distinct de la création du compte SI-SEP.
    profil_utilisateur n'est renseigné que lorsque la Division crée un compte pour ce médecin.
    """
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ligue = models.ForeignKey(
        'Institution',
        on_delete=models.CASCADE,
        related_name='medecins_ligue',
        limit_choices_to={'niveau_territorial__in': ['LIGUE', 'LIGUE_PROVINCIALE']},
        help_text='Ligue provinciale à laquelle le médecin est rattaché'
    )
    agent = models.OneToOneField(
        'Agent',
        on_delete=models.CASCADE,
        related_name='medecin_ligue',
        help_text='Agent (Personne) enregistré comme médecin de la ligue'
    )
    numero_ordre_medecins = models.CharField(
        max_length=50,
        help_text="Numéro de l'Ordre des Médecins"
    )
    profil_utilisateur = models.OneToOneField(
        'core.ProfilUtilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medecin_ligue',
        help_text='Compte SI-SEP du médecin (créé par la Division) ; vide si pas encore de compte'
    )
    date_enregistrement = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'medecin_ligue'
        verbose_name = 'Médecin de Ligue'
        verbose_name_plural = 'Médecins de Ligue'
        ordering = ['ligue__nom_officiel', 'agent__personne__nom']

    def __str__(self):
        return f"{self.agent.personne.nom_complet} — {self.ligue.nom_officiel}"

    @property
    def a_un_compte(self):
        return self.profil_utilisateur_id is not None
