# -*- coding: utf-8 -*-
"""
Modèle ResultatExamenVisite - SI-SEP Sport RDC.
Résultat d'un type d'examen pour une visite médicale donnée.
Le médecin en consultation pioche dans TypeExamen et enregistre ici le résultat.
"""
from django.db import models


class ResultatExamenVisite(models.Model):
    """
    Résultat d'un examen (TypeExamen) pour une visite médicale (F67).
    Une visite peut avoir plusieurs ResultatExamenVisite (un par type d'examen réalisé).
    """
    visite_medicale = models.ForeignKey(
        'VisiteMedicale',
        on_delete=models.CASCADE,
        related_name='resultats_examens',
        help_text='Visite médicale concernée'
    )
    type_examen = models.ForeignKey(
        'TypeExamen',
        on_delete=models.PROTECT,
        related_name='resultats_visites',
        help_text='Type d\'examen réalisé'
    )
    resultat_ok = models.BooleanField(
        null=True,
        blank=True,
        help_text='Résultat conforme (True) ou non conforme (False). Null = non renseigné.'
    )
    valeur_texte = models.CharField(
        max_length=500,
        blank=True,
        help_text='Valeur textuelle (ex. 120/80 pour tension, 10/10 pour acuité)'
    )
    fichier = models.FileField(
        upload_to='athletes/visites_medicales/resultats_examens/',
        null=True,
        blank=True,
        help_text='Document joint si le type d\'examen accepte un fichier'
    )

    class Meta:
        db_table = 'resultat_examen_visite'
        verbose_name = 'Résultat examen (visite)'
        verbose_name_plural = 'Résultats examens (visite)'
        unique_together = [['visite_medicale', 'type_examen']]
        ordering = ['type_examen__ordre', 'type_examen__libelle']

    def __str__(self):
        return f"{self.visite_medicale} — {self.type_examen}"
