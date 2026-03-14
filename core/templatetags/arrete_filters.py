"""
Filtres de template personnalisés pour les arrêtés ministériels
"""
from django import template
from datetime import timedelta
from dateutil.relativedelta import relativedelta

register = template.Library()


@register.filter
def get_item(d, key):
    """Accès à un dictionnaire par clé (variable). Usage: {{ form_data|get_item:key }}"""
    if d is None:
        return None
    return d.get(key) if hasattr(d, 'get') else None


@register.filter
def add_years(date, years):
    """
    Ajoute un nombre d'années à une date.
    Usage: {{ date|add_years:4 }}
    """
    if not date or not years:
        return "—"
    try:
        # Utiliser relativedelta pour gérer correctement les années bissextiles
        new_date = date + relativedelta(years=int(years))
        return new_date.strftime('%d/%m/%Y')
    except:
        return "—"
