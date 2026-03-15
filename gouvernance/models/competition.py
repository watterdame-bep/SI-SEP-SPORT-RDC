# -*- coding: utf-8 -*-
"""
Modèles Compétition - SI-SEP Sport RDC.
Types de compétition gérés par la ligue, compétitions par saison, calendrier.
Séparé des « événements » (matchs, galas ponctuels) du module infrastructures.
"""
import uuid
from django.db import models


class TypeCompetition(models.Model):
    """
    Type de compétition enregistré par la ligue (ex: Championnat provincial, Coupe, Tournoi).
    Chaque ligue gère sa propre liste de types.
    """
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ligue = models.ForeignKey(
        'gouvernance.Institution',
        on_delete=models.CASCADE,
        related_name='types_competition',
        limit_choices_to={'niveau_territorial': 'LIGUE'},
        help_text='Ligue qui enregistre ce type',
    )
    designation = models.CharField(
        max_length=255,
        help_text='Intitulé du type (ex: Championnat provincial, Coupe de la ligue)',
    )
    code = models.CharField(max_length=50, blank=True, help_text='Code court optionnel')
    ordre = models.PositiveSmallIntegerField(default=0, help_text='Ordre d\'affichage')
    actif = models.BooleanField(default=True)

    class Meta:
        db_table = 'type_competition'
        verbose_name = 'Type de compétition'
        verbose_name_plural = 'Types de compétition'
        ordering = ['ligue', 'ordre', 'designation']
        unique_together = [['ligue', 'designation']]

    def __str__(self):
        if self.code:
            return f"{self.code} — {self.designation}"
        return self.designation


class Competition(models.Model):
    """
    Compétition provinciale créée par la ligue, liée à un type et une saison (année sportive).
    Ex: « Championnat provincial 2024-2025 ». Catégorie Junior/Sénior.
    """
    CATEGORIE_CHOICES = [
        ('JUNIOR', 'Junior'),
        ('SENIOR', 'Sénior'),
        ('TOUS', 'Toutes catégories'),
    ]
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type_competition = models.ForeignKey(
        TypeCompetition,
        on_delete=models.PROTECT,
        related_name='competitions',
        help_text='Type de compétition (Championnat, Coupe, etc.)',
    )
    organisateur = models.ForeignKey(
        'gouvernance.Institution',
        on_delete=models.CASCADE,
        related_name='competitions_organisees',
        limit_choices_to={'niveau_territorial': 'LIGUE'},
        help_text='Ligue organisatrice',
    )
    saison = models.CharField(
        max_length=20,
        help_text='Saison / année sportive (ex: 2024-2025 ou 2024)',
    )
    categorie = models.CharField(
        max_length=20,
        choices=CATEGORIE_CHOICES,
        default='SENIOR',
        help_text='Catégorie (Junior, Sénior)',
    )
    titre = models.CharField(
        max_length=255,
        help_text='Titre de la compétition (ex: Championnat provincial Kinshasa 2024-2025)',
    )
    description = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    actif = models.BooleanField(default=True)

    class Meta:
        db_table = 'competition'
        verbose_name = 'Compétition'
        verbose_name_plural = 'Compétitions'
        ordering = ['-saison', 'titre']

    def __str__(self):
        return f"{self.titre} ({self.saison})"


class Journee(models.Model):
    """
    Journée ou phase d'une compétition (ex: 1ère Journée, Phase de poules).
    Regroupe les rencontres (matchs).
    """
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey(
        Competition,
        on_delete=models.CASCADE,
        related_name='journees',
        help_text='Compétition concernée',
    )
    libelle = models.CharField(
        max_length=255,
        help_text='Ex: 1ère Journée, Phase de poules, Demi-finale',
    )
    ordre = models.PositiveSmallIntegerField(default=0, help_text='Ordre d\'affichage')

    class Meta:
        db_table = 'journee'
        verbose_name = 'Journée'
        verbose_name_plural = 'Journées'
        ordering = ['competition', 'ordre', 'libelle']

    def __str__(self):
        return f"{self.competition.titre} — {self.libelle}"


class Rencontre(models.Model):
    """
    Match (affiche) : Club A vs Club B, stade, date/heure.
    Un stade ne peut pas recevoir deux rencontres au même créneau (validé en clean).
    À la création, un Événement billetterie est créé pour que le gestionnaire d'infrastructure puisse ouvrir les ventes.
    """
    STATUT_CHOICES = [
        ('PROGRAMME', 'Programmé'),
        ('EN_COURS', 'En cours'),
        ('TERMINE', 'Terminé'),
        ('REPORTE', 'Reporté'),
    ]
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    journee = models.ForeignKey(
        Journee,
        on_delete=models.CASCADE,
        related_name='rencontres',
        help_text='Journée ou phase',
    )
    equipe_a = models.ForeignKey(
        'gouvernance.Institution',
        on_delete=models.PROTECT,
        related_name='rencontres_domicile',
        limit_choices_to={'niveau_territorial': 'CLUB'},
        help_text='Club (équipe A)',
    )
    equipe_b = models.ForeignKey(
        'gouvernance.Institution',
        on_delete=models.PROTECT,
        related_name='rencontres_exterieur',
        limit_choices_to={'niveau_territorial': 'CLUB'},
        help_text='Club (équipe B)',
    )
    stade = models.ForeignKey(
        'infrastructures.Infrastructure',
        on_delete=models.PROTECT,
        related_name='rencontres',
        null=True,
        blank=True,
        help_text='Stade / infrastructure (réservation du créneau)',
    )
    date_heure = models.DateTimeField(help_text='Date et heure du match')
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='PROGRAMME',
    )
    evenement = models.OneToOneField(
        'infrastructures.Evenement',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rencontre',
        help_text='Événement billetterie créé automatiquement pour ce match',
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rencontre'
        verbose_name = 'Rencontre'
        verbose_name_plural = 'Rencontres'
        ordering = ['date_heure']

    def __str__(self):
        return f"{self.equipe_a.nom_officiel} vs {self.equipe_b.nom_officiel} — {self.date_heure}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.stade_id and self.date_heure:
            qs = Rencontre.objects.filter(
                stade_id=self.stade_id,
                date_heure=self.date_heure,
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    {'date_heure': 'Ce stade a déjà une rencontre à cette date et heure.'}
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and self.stade_id and not self.evenement_id:
            from infrastructures.models import Evenement
            titre = f"{self.equipe_a.nom_officiel} vs {self.equipe_b.nom_officiel}"
            evenement = Evenement.objects.create(
                infrastructure_id=self.stade_id,
                organisateur_id=self.journee.competition.organisateur_id,
                titre=titre[:255],
                type_evenement='MATCH',
                date_evenement=self.date_heure.date(),
                heure_debut=self.date_heure.time(),
                description=f"Match {self.journee.libelle} — {self.journee.competition.titre}",
                actif=True,
            )
            self.evenement = evenement
            Rencontre.objects.filter(pk=self.pk).update(evenement_id=evenement.uid)


class CalendrierCompetition(models.Model):
    """
    Une date du calendrier d'une compétition (journée, phase, match à date fixe).
    Permet à la ligue de construire le calendrier d'une compétition provinciale.
    """
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey(
        Competition,
        on_delete=models.CASCADE,
        related_name='calendrier',
        help_text='Compétition concernée',
    )
    date = models.DateField(help_text='Date prévue')
    heure_debut = models.TimeField(null=True, blank=True)
    libelle = models.CharField(
        max_length=255,
        help_text='Ex: Journée 1, Phase de poules, Demi-finale',
    )
    infrastructure = models.ForeignKey(
        'infrastructures.Infrastructure',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='calendrier_competitions',
        help_text='Lieu prévu (stade/terrain)',
    )
    ordre = models.PositiveSmallIntegerField(default=0, help_text='Ordre dans le calendrier')

    class Meta:
        db_table = 'calendrier_competition'
        verbose_name = 'Date du calendrier'
        verbose_name_plural = 'Calendrier compétition'
        ordering = ['competition', 'date', 'ordre', 'libelle']

    def __str__(self):
        return f"{self.competition.titre} — {self.date} {self.libelle}"
