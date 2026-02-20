"""
Modèles du module Gouvernance - SI-SEP Sport RDC.
Hiérarchie : État (Ministère/Division Provinciale) -> Fédérations -> Ligues -> Clubs.
Validation à double niveau : Sportif (Ligue/Fédé) et Administratif (Division Provinciale).
"""
from .localisation import (
    ProvAdmin,
    TerritoireVille,
    SecteurCommune,
    GroupementQuartier,
    VillageQuartier,
)
from .institution import TypeInstitution, Institution
from .agrement import EtatAgrement, EtatAdministrative
from .contact import AdresseContact
from .personne import Personne
from .organigramme import Fonction, Membre, Mandat

__all__ = [
    'TerritoireVille',
    'ProvAdmin',
    'SecteurCommune',
    'GroupementQuartier',
    'VillageQuartier',
    'TypeInstitution',
    'Institution',
    'EtatAgrement',
    'EtatAdministrative',
    'AdresseContact',
    'Personne',
    'Fonction',
    'Membre',
    'Mandat',
]
