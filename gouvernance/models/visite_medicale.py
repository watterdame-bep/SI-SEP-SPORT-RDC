# -*- coding: utf-8 -*-
"""
Modèle Visite Médicale (F67) - SI-SEP Sport RDC.
Conforme au catalogue Module 6 : examen médical pour homologation et délivrance de licence.
Une visite médicale est liée à un athlète ; si resultat_global = INAPTE, la génération de licence est bloquée.
"""
import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class VisiteMedicale(models.Model):
    """
    Fiche de visite médicale (F67) : examen clinique, tests de sécurité, certificat d'aptitude (F72).
    Obligatoire pour valider l'enrôlement et la délivrance de licence.
    """
    RESULTAT_GLOBAL_CHOICES = [
        ('APTE', 'Apte'),
        ('INAPTE', 'Inapte'),
        ('APTE_AVEC_RESERVE', 'Apte avec réserve'),
    ]

    athlete = models.ForeignKey(
        'Athlete',
        on_delete=models.CASCADE,
        related_name='visites_medicales',
        help_text='Athlète concerné par cette visite'
    )
    date_visite = models.DateField(help_text='Date de la visite médicale')
    medecin_nom = models.CharField(max_length=200, help_text='Nom du médecin (examen provincial)')
    medecin_etablissement = models.CharField(
        max_length=255,
        blank=True,
        help_text='Établissement ou centre de santé'
    )
    medecin_numero_ordre = models.CharField(
        max_length=50,
        blank=True,
        help_text='Numéro d\'Ordre des Médecins (traçabilité, visible par la Ligue)'
    )
    recommandations_securite = models.TextField(
        blank=True,
        help_text='Recommandations visibles par la Ligue uniquement (sécurité, équipement, ex: "Doit porter des lunettes de protection")'
    )

    # ---------- Résultat global (F72) ----------
    resultat_global = models.CharField(
        max_length=20,
        choices=RESULTAT_GLOBAL_CHOICES,
        default='APTE',
        help_text='Conclusion du médecin : Apte / Inapte / Apte avec réserve'
    )

    # ---------- 1. Examen clinique général (F67) — Biométrie ----------
    taille_cm = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(50), MaxValueValidator(250)],
        help_text='Taille en cm'
    )
    poids_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(300)],
        help_text='Poids en kg'
    )
    # IMC calculé automatiquement si taille et poids renseignés
    imc = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Indice de masse corporelle (calculé)'
    )

    # ---------- Cardio-respiratoire et tension ----------
    aptitude_cardiaque = models.BooleanField(
        null=True,
        blank=True,
        help_text='Auscultation cœur et poumons au repos : conforme'
    )
    tension_systolique = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(80), MaxValueValidator(250)],
        help_text='Tension artérielle systolique (mmHg)'
    )
    tension_diastolique = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(40), MaxValueValidator(150)],
        help_text='Tension artérielle diastolique (mmHg)'
    )
    examen_osteo_articulaire_ok = models.BooleanField(
        default=True,
        help_text='Colonne, articulations (genoux, chevilles), souplesse : OK'
    )
    notes_examen_clinique = models.TextField(blank=True, help_text='Remarques du médecin')

    # ---------- 2. Tests de sécurité (obligatoires SI-SEP) ----------
    ecg_joint = models.FileField(
        upload_to='athletes/visites_medicales/ecg/',
        null=True,
        blank=True,
        help_text='ECG de repos (obligatoire pour prévention mort subite)'
    )
    ecg_normal = models.BooleanField(
        null=True,
        blank=True,
        help_text='ECG interprété comme normal (True) ou anormal (False)'
    )
    groupe_sanguin_rh = models.CharField(
        max_length=10,
        blank=True,
        help_text='Groupe sanguin et Rhésus (ex: A+, O-) pour licence F22'
    )
    acuite_visuelle = models.CharField(
        max_length=100,
        blank=True,
        help_text='Acuité visuelle (ex: 10/10 OD, 10/10 OG)'
    )
    acuite_auditive = models.CharField(
        max_length=100,
        blank=True,
        help_text='Acuité auditive ou mention "normale"'
    )

    # ---------- 3. Examens biologiques (laboratoire) ----------
    hemogramme_ok = models.BooleanField(null=True, blank=True, help_text='NFS / hémogramme complet : normal')
    hemogramme_fichier = models.FileField(
        upload_to='athletes/visites_medicales/hemogramme/',
        null=True,
        blank=True
    )
    examen_urines_ok = models.BooleanField(
        null=True,
        blank=True,
        help_text='Glycosurie / protéinurie : normal'
    )
    examen_urines_fichier = models.FileField(
        upload_to='athletes/visites_medicales/urines/',
        null=True,
        blank=True
    )

    # ---------- 4. Certification F72 — Certificat d'aptitude ----------
    certificat_aptitude_joint = models.FileField(
        upload_to='athletes/visites_medicales/certificats_aptitude/',
        null=True,
        blank=True,
        help_text='Certificat d\'aptitude (F72) scanné — obligatoire pour valider la licence'
    )
    certificat_aptitude_delivre = models.BooleanField(
        default=False,
        help_text='Certificat d\'aptitude délivré (coché). Obligatoire pour validation licence.'
    )

    # ---------- 5. Surclassement (cadet/junior → senior) ----------
    demande_surclassement = models.BooleanField(
        default=False,
        help_text='Demande de surclassement (ex: Cadet/Junior en Senior)'
    )
    radiographie_poignet_joint = models.FileField(
        upload_to='athletes/visites_medicales/surclassement/',
        null=True,
        blank=True,
        help_text='Radiographie poignet (test de Greulich et Pyle)'
    )
    test_greulich_pyle_ok = models.BooleanField(
        null=True,
        blank=True,
        help_text='Âge osseux compatible avec le surclassement'
    )

    # ---------- Métadonnées ----------
    uid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text='Identifiant public pour vérification du certificat (QR code)'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'core.ProfilUtilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='visites_medicales_creées'
    )

    class Meta:
        db_table = 'visite_medicale'
        verbose_name = 'Visite médicale (F67)'
        verbose_name_plural = 'Visites médicales (F67)'
        ordering = ['-date_visite']

    def __str__(self):
        return f"Visite {self.date_visite} — {self.athlete} — {self.get_resultat_global_display()}"

    def save(self, *args, **kwargs):
        if self.taille_cm and self.poids_kg and self.poids_kg > 0:
            taille_m = Decimal(self.taille_cm) / 100
            self.imc = (self.poids_kg / (taille_m * taille_m)).quantize(Decimal('0.01'))
        else:
            self.imc = None
        super().save(*args, **kwargs)

    def peut_generer_licence(self):
        """
        Le système ne doit pas autoriser la génération de licence si :
        - resultat_global == 'INAPTE'
        - certificat d'aptitude non délivré ou document non joint
        """
        if self.resultat_global == 'INAPTE':
            return False
        if not self.certificat_aptitude_delivre:
            return False
        if not self.certificat_aptitude_joint:
            return False
        return True
