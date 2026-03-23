# -*- coding: utf-8 -*-
"""
Arbitre sportif enregistré dans le système SI-SEP.
Enregistrement en tant qu'agent, séparé de la création de compte.
"""
import uuid
from django.db import models


class Arbitre(models.Model):
    NIVEAU_CHOICES = [
        ('PROVINCIAL', 'Provincial'),
        ('NATIONAL', 'National'),
        ('INTERNATIONAL', 'International'),
    ]

    CATEGORIE_CHOICES = [
        ('STAGIAIRE', 'Stagiaire'),
        ('ELITE', 'Élite'),
        ('PROFESSIONNEL', 'Professionnel'),
    ]

    STATUT_CHOICES = [
        ('EN_ATTENTE_MEDICALE', 'En attente médicale'),
        ('INSTRUIT', 'Instruit (médical OK)'),
        ('INAPTE', 'Inapte (médical)'),
        ('ACTIF', 'Actif (licence délivrée)'),
        ('SUSPENDU', 'Suspendu'),
        ('INACTIF', 'Inactif'),
    ]

    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    personne = models.OneToOneField(
        'gouvernance.Personne',
        on_delete=models.CASCADE,
        related_name='arbitre',
    )

    discipline = models.ForeignKey(
        'gouvernance.DisciplineSport',
        on_delete=models.PROTECT,
        related_name='arbitres',
        null=True,
        blank=True,
    )

    institution = models.ForeignKey(
        'gouvernance.Institution',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='arbitres',
        help_text='Ligue ou Fédération qui a enregistré l\'arbitre',
    )

    numero_licence = models.CharField(max_length=50, blank=True, unique=True, null=True)
    niveau = models.CharField(max_length=20, choices=NIVEAU_CHOICES, default='PROVINCIAL')
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, default='DEUXIEME')
    statut = models.CharField(max_length=30, choices=STATUT_CHOICES, default='EN_ATTENTE_MEDICALE')

    # Photos (face + profils)
    photo = models.ImageField(
        upload_to='arbitres/photos/',
        null=True, blank=True,
        help_text='Photo de face'
    )
    photo_gauche = models.ImageField(
        upload_to='arbitres/photos/',
        null=True, blank=True,
        help_text='Profil gauche'
    )
    photo_droite = models.ImageField(
        upload_to='arbitres/photos/',
        null=True, blank=True,
        help_text='Profil droit'
    )

    # Empreintes digitales — standard 4-4-2 (images + templates minuties)
    empreintes_capturees = models.BooleanField(default=False)
    empreintes_template = models.TextField(
        blank=True,
        help_text='Template d\'empreintes digitales (base64 JSON — legacy)'
    )
    # Images des 3 prises
    main_droite_4 = models.ImageField(upload_to='arbitres/empreintes/%Y/%m/', null=True, blank=True, help_text='4 doigts main droite')
    main_gauche_4 = models.ImageField(upload_to='arbitres/empreintes/%Y/%m/', null=True, blank=True, help_text='4 doigts main gauche')
    pouces_2     = models.ImageField(upload_to='arbitres/empreintes/%Y/%m/', null=True, blank=True, help_text='2 pouces')
    # Templates minuties (BinaryField) pour comparaison 1:N
    main_droite_4_template = models.BinaryField(null=True, blank=True)
    main_gauche_4_template = models.BinaryField(null=True, blank=True)
    pouces_2_template      = models.BinaryField(null=True, blank=True)

    # Certificat médical généré après verdict (PDF)
    certificat_medical = models.FileField(
        upload_to='arbitres/certificats/%Y/%m/',
        null=True, blank=True,
        help_text='Certificat médical PDF généré par le médecin'
    )

    # Résultat médical (rempli par le médecin de la ligue)
    resultat_medical = models.CharField(
        max_length=20,
        choices=[('APTE', 'Apte'), ('INAPTE', 'Inapte'), ('APTE_AVEC_RESERVE', 'Apte avec réserve')],
        null=True,
        blank=True,
    )
    notes_medicales = models.TextField(blank=True, help_text='Observations du médecin (visibles par la ligue)')
    date_examen_medical = models.DateField(null=True, blank=True)

    date_naissance = models.DateField(null=True, blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)

    date_enregistrement = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'arbitre'
        verbose_name = 'Arbitre'
        verbose_name_plural = 'Arbitres'
        ordering = ['personne__nom', 'personne__prenom']

    def __str__(self):
        return f"{self.personne.nom_complet} — {self.get_niveau_display()}"

    def generer_numero_licence(self):
        """Génère un numéro de licence unique pour l'arbitre."""
        from datetime import date
        annee = date.today().year
        count = Arbitre.objects.filter(date_enregistrement__year=annee).count() + 1
        numero = f"ARB-{annee}-{count:05d}"
        while Arbitre.objects.filter(numero_licence=numero).exists():
            count += 1
            numero = f"ARB-{annee}-{count:05d}"
        return numero
