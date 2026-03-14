from django.apps import AppConfig


class GouvernanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gouvernance'
    verbose_name = 'Gouvernance (Institutions, Agréments, Organigrammes)'
    
    def ready(self):
        """Enregistrer les signaux."""
        import gouvernance.signals  # noqa
