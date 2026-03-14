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
)
from .institution import TypeInstitution, Institution
from .agrement import EtatAgrement, EtatAdministrative
from .contact import AdresseContact
from .personne import Personne
from .agent import Agent
from .organigramme import Fonction, Membre, Mandat
from .discipline import DisciplineSport
from .chef_division import DivisionProvinciale
from .validation_federation import ValidationFederation
from .validation_ligue import ValidationLigue, AttestationReconnaissance
from .club_validation import ClubValidation
from .athlete import Athlete
from .visite_medicale import VisiteMedicale
from .medecin_ligue import MedecinLigue
from .capture_empreintes import CaptureEmpreintes
from .type_examen import TypeExamen
from .resultat_examen_visite import ResultatExamenVisite
from .competition import TypeCompetition, Competition, Journee, Rencontre, CalendrierCompetition

__all__ = [
    'TerritoireVille',
    'ProvAdmin',
    'SecteurCommune',
    'GroupementQuartier',
    'TypeInstitution',
    'Institution',
    'EtatAgrement',
    'EtatAdministrative',
    'AdresseContact',
    'Personne',
    'Agent',
    'Fonction',
    'Membre',
    'Mandat',
    'DisciplineSport',
    'DivisionProvinciale',
    'ValidationFederation',
    'ValidationLigue',
    'AttestationReconnaissance',
    'ClubValidation',
    'Athlete',
    'VisiteMedicale',
    'MedecinLigue',
    'CaptureEmpreintes',
    'TypeExamen',
    'ResultatExamenVisite',
    'TypeCompetition',
    'Competition',
    'Journee',
    'Rencontre',
    'CalendrierCompetition',
]
