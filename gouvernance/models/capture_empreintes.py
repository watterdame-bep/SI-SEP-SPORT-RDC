# -*- coding: utf-8 -*-
"""
Modèle de capture des empreintes digitales — Standard 4-4-2 (SI-SEP Sport RDC).
Images : audit / affichage. Templates (BinaryField) : signatures numériques (minuties) du SDK
pour comparaison 1:N et lutte contre la fraude en temps réel (ANSI 378, ISO 19794-2, etc.).
"""
from django.db import models


class CaptureEmpreintes(models.Model):
    """
    Capture des 10 doigts (standard 4-4-2). Images pour audit ; templates (minuties) pour
    comparaison rapide et détection de doublons / fraude en temps réel.
    """
    athlete = models.OneToOneField(
        'Athlete',
        on_delete=models.CASCADE,
        related_name='capture_empreintes',
        help_text='Athlète concerné',
    )
    date_capture = models.DateTimeField(auto_now_add=True)
    captured_by = models.ForeignKey(
        'core.ProfilUtilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='captures_empreintes',
        help_text='Agent ligue ayant effectué le prélèvement',
    )

    # 4 doigts main droite (index, majeur, annulaire, auriculaire) — une image du lecteur
    main_droite_4 = models.ImageField(
        upload_to='empreintes/%Y/%m/',
        null=True,
        blank=True,
        help_text='4 doigts main droite — posés simultanément à plat',
    )
    # 4 doigts main gauche
    main_gauche_4 = models.ImageField(
        upload_to='empreintes/%Y/%m/',
        null=True,
        blank=True,
        help_text='4 doigts main gauche — posés simultanément à plat',
    )
    # 2 pouces (droite + gauche)
    pouces_2 = models.ImageField(
        upload_to='empreintes/%Y/%m/',
        null=True,
        blank=True,
        help_text='2 pouces — posés simultanément ou l\'un après l\'autre',
    )

    # ---------- Templates (minuties / signatures numériques — pour comparaison 1:N et anti-fraude) ----------
    # Binaire fourni par le SDK (ANSI 378, ISO 19794-2 ou propriétaire). Si base64, décoder avant sauvegarde.
    main_droite_4_template = models.BinaryField(
        null=True,
        blank=True,
        help_text='Template 4 doigts main droite — comparaison rapide et détection fraude.',
    )
    main_gauche_4_template = models.BinaryField(
        null=True,
        blank=True,
        help_text='Template 4 doigts main gauche.',
    )
    pouces_2_template = models.BinaryField(
        null=True,
        blank=True,
        help_text='Template 2 pouces.',
    )

    class Meta:
        db_table = 'capture_empreintes'
        verbose_name = 'Capture d’empreintes (10 doigts)'
        verbose_name_plural = 'Captures d’empreintes (10 doigts)'

    def __str__(self):
        return f"Empreintes — {self.athlete} — {self.date_capture.date()}"

    @property
    def is_complete(self):
        """Vérifie que les 3 prises (images et/ou templates) ont été enregistrées."""
        has_images = bool(self.main_droite_4 and self.main_gauche_4 and self.pouces_2)
        has_templates = bool(
            self.main_droite_4_template and self.main_gauche_4_template and self.pouces_2_template
        )
        return has_images or has_templates

    @property
    def has_templates(self):
        """Vérifie que les 3 templates sont présents — nécessaire pour la recherche / anti-fraude 1:N."""
        return bool(
            self.main_droite_4_template and self.main_gauche_4_template and self.pouces_2_template
        )
