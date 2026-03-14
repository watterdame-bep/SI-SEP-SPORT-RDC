# -*- coding: utf-8 -*-
"""
Modèle TypeExamen - SI-SEP Sport RDC.
Liste des types d'examens médicaux (référentiel). Remplie par le Médecin Inspecteur.
Les médecins qui font les consultations piochent dans cette liste pour enregistrer les résultats.
"""
from django.db import models


class TypeExamen(models.Model):
    """
    Type d'examen médical (ex. ECG, Tension artérielle, Acuité visuelle).
    Référentiel commun : le Médecin Inspecteur ajoute/modifie les types ;
    les médecins en consultation sélectionnent dans cette liste et renseignent le résultat.
    """
    libelle = models.CharField(
        max_length=255,
        help_text='Intitulé du type d\'examen (ex. Électrocardiogramme (ECG))'
    )
    code = models.CharField(
        max_length=50,
        blank=True,
        help_text='Code court optionnel (ex. ECG, NFS)'
    )
    description = models.TextField(
        blank=True,
        help_text='Description ou précisions pour le médecin'
    )
    obligatoire = models.BooleanField(
        default=True,
        help_text='Examen obligatoire pour la visite d\'homologation'
    )
    ordre = models.PositiveIntegerField(
        default=0,
        help_text='Ordre d\'affichage dans le formulaire (plus petit = plus haut)'
    )
    actif = models.BooleanField(
        default=True,
        help_text='Inactif = masqué dans le formulaire de consultation'
    )
    accepte_fichier = models.BooleanField(
        default=False,
        help_text='Le médecin peut joindre un document pour ce type d\'examen'
    )

    class Meta:
        db_table = 'type_examen'
        verbose_name = 'Type d\'examen médical'
        verbose_name_plural = 'Types d\'examens médicaux'
        ordering = ['ordre', 'libelle']

    def __str__(self):
        if self.code:
            return f"{self.code} — {self.libelle}"
        return self.libelle
