from django.urls import path
from . import views_federations, views_disciplines, views_personnel, views_dashboards, views_arretes, views_courriers, views_divisions, views_validation_federation, views_verify, views_federation_secretary, views_sg_ligues, views_division_ligues, views_ligue_secretary, views_club_secretary, views_medecin_division, views_medecin_ligue, views_competitions
from .views_club_validation import clubs_en_attente_validation, club_validation_detail

app_name = 'gouvernance'

urlpatterns = [
    # Vérification publique des documents (root-level pour QR codes)
    path('verify/', views_verify.verify_home, name='verify_home'),
    path('verify/arrete/<str:numero_arrete>/', views_verify.verify_arrete_by_numero, name='verify_arrete_numero'),
    path('verify/certificat/<str:numero_homologation>/', views_verify.verify_certificat_by_numero, name='verify_certificat_numero'),
    
    # Vérification par UUID (depuis QR codes)
    path('verifier-arrete/<uuid:uid>/', views_arretes.verifier_arrete, name='verifier_arrete_uuid'),
    path('verifier-certificat/<uuid:uid>/', views_verify.verify_certificat_by_uuid, name='verify_certificat_uuid'),
    path('verifier-ligue/<uuid:uid>/', views_verify.verify_ligue_by_uuid, name='verify_ligue_uuid'),
    path('certificat-aptitude/verifier/<uuid:uid>/', views_verify.verifier_certificat_aptitude, name='verifier_certificat_aptitude'),
    path('verifier-athlete/<uuid:uid>/', views_verify.verifier_athlete, name='verifier_athlete'),
    
    # Dashboards
    path('dashboard/sg/', views_dashboards.sg_dashboard, name='sg_dashboard'),
    path('dashboard/ministre/', views_dashboards.minister_dashboard, name='minister_dashboard'),
    path('dashboard/directeur-provincial/', views_dashboards.directeur_provincial_dashboard, name='directeur_provincial_dashboard'),
    path('enquetes-viabilite/', views_dashboards.enquetes_viabilite, name='enquetes_viabilite'),
    path('inspections-a-transferer/', views_dashboards.inspections_a_transferer, name='inspections_a_transferer'),
    
    # Arrêtés
    path('arretes/', views_arretes.minister_arretes, name='minister_arretes'),
    path('arretes/download/<uuid:pk>/', views_arretes.download_arrete, name='download_arrete'),
    path('arretes/verify/<uuid:uid>/', views_arretes.verifier_arrete, name='verifier_arrete'),
    
    # Courriers & Parapheur
    path('courriers/', views_courriers.minister_courriers, name='minister_courriers'),
    path('courriers/<uuid:pk>/', views_courriers.parapheur_detail, name='parapheur_detail'),
    path('courriers/<uuid:uid>/signer/', views_courriers.signer_courrier, name='signer_courrier'),
    path('courriers/<uuid:uid>/refuser/', views_courriers.refuser_courrier, name='refuser_courrier'),
    path('certificats/download/<uuid:pk>/', views_courriers.download_certificat, name='download_certificat'),
    path('certificats/verify/<str:numero_homologation>/', views_courriers.verifier_certificat, name='verifier_certificat'),
    
    # Profil Ministre
    path('profil/ministre/', views_courriers.profil_ministre, name='profil_ministre'),
    
    # Profil Secrétaire Général
    path('profil/sg/', views_courriers.profil_sg, name='profil_sg'),
    
    # Fédérations Nationales
    path('federations/', views_federations.federations_nationales, name='federations_nationales'),
    path('federations/create/', views_federations.federation_create, name='federation_create'),
    path('federations/store/', views_federations.federation_store, name='federation_store'),
    path('federations/<uuid:pk>/', views_federations.federation_detail, name='federation_detail'),
    path('federations/<uuid:pk>/arrete/', views_federations.federation_download_arrete, name='federation_download_arrete'),
    path('federations/<uuid:pk>/download-arrete/', views_federations.federation_download_arrete, name='federation_download_arrete'),
    path('federations/<uuid:pk>/download-certificat/', views_federations.federation_download_certificat, name='federation_download_certificat'),
    path('federations/<uuid:pk>/delete/', views_federations.federation_delete, name='federation_delete'),
    
    # Validation des Fédérations par Directeurs Provinciaux
    path('validations/<uuid:uid>/', views_validation_federation.validation_detail, name='validation_detail'),
    path('validations/<uuid:uid>/submit/', views_validation_federation.validation_submit, name='validation_submit'),
    path('validations/<uuid:uid>/transfer/', views_validation_federation.validation_transfer_to_minister, name='validation_transfer'),
    # SG : consulter une inspection validée par la province avant transfert au Ministre
    path('sg/validations/<uuid:uid>/', views_validation_federation.sg_validation_verifier, name='sg_validation_verifier'),
    
    # Paramètres Disciplines
    path('parametres/disciplines/', views_disciplines.parametres_disciplines, name='parametres_disciplines'),
    path('parametres/disciplines/create/', views_disciplines.discipline_create, name='discipline_create'),
    path('parametres/disciplines/<uuid:uid>/update/', views_disciplines.discipline_update, name='discipline_update'),
    path('parametres/disciplines/<uuid:uid>/delete/', views_disciplines.discipline_delete, name='discipline_delete'),
    path('parametres/disciplines/<uuid:uid>/toggle/', views_disciplines.discipline_toggle_actif, name='discipline_toggle_actif'),
    
    # Gestion du Personnel du Cabinet (SG)
    path('personnel/', views_personnel.personnel_ministere, name='personnel_ministere'),
    path('personnel/enregistrer/', views_personnel.enregistrer_agent, name='enregistrer_agent'),
    path('personnel/<uuid:agent_id>/', views_personnel.detail_agent, name='detail_agent'),
    path('personnel/<uuid:agent_id>/modifier/', views_personnel.modifier_agent, name='modifier_agent'),
    path('personnel/<uuid:agent_id>/creer-acces/', views_personnel.creer_acces_systeme, name='creer_acces_systeme'),
    path('personnel/<uuid:agent_id>/desactiver/', views_personnel.desactiver_compte, name='desactiver_compte'),
    path('personnel/<uuid:agent_id>/reactiver/', views_personnel.reactiver_compte, name='reactiver_compte'),
    path('personnel/<uuid:agent_id>/mandat/', views_personnel.creer_mandat, name='creer_mandat'),
    
    # Divisions Provinciales
    path('divisions/', views_divisions.divisions_provinciales, name='divisions_provinciales'),
    path('divisions/<uuid:division_id>/', views_divisions.division_detail, name='division_detail'),
    
    # Tableau de bord Secrétaire de Fédération
    path('federation/dashboard/', views_federation_secretary.federation_secretary_dashboard, name='federation_secretary_dashboard'),
    path('federation/clubs/', views_federation_secretary.federation_clubs_list, name='federation_clubs'),
    path('federation/ligues/', views_federation_secretary.federation_ligues_list, name='federation_ligues'),
    path('federation/ligues/create/', views_federation_secretary.create_ligue_provincial, name='create_ligue_provincial'),
    path('federation/documents/', views_federation_secretary.federation_documents, name='federation_documents'),
    path('federation/profil/', views_federation_secretary.federation_profile, name='federation_profile'),
    path('federation/athletes/', views_federation_secretary.federation_athletes, name='federation_athletes'),
    path('federation/competitions/', views_federation_secretary.federation_competitions, name='federation_competitions'),
    path('federation/ordre-mission/', views_federation_secretary.federation_ordre_mission, name='federation_ordre_mission'),
    
    # Validation des athlètes par la Fédération
    path('federation/athletes/validation/', views_federation_secretary.federation_athletes_validation_list, name='federation_athletes_validation_list'),
    path('federation/athletes/<uuid:athlete_uid>/validate/', views_federation_secretary.federation_athlete_validate, name='federation_athlete_validate'),
    path('federation/athletes/<uuid:athlete_uid>/licence-print/', views_club_secretary.licence_f22_print, name='federation_licence_f22_print'),
    path('federation/athletes/<uuid:athlete_uid>/verify-duplicates/', views_federation_secretary.federation_athlete_verify_duplicates, name='federation_athlete_verify_duplicates'),
    
    # Secrétaire Général - Gestion des Ligues Provinciales
    path('sg/ligues/', views_sg_ligues.sg_ligues_en_attente, name='sg_ligues_en_attente'),
    path('sg/ligues/<uuid:ligue_id>/', views_sg_ligues.sg_ligue_detail, name='sg_ligue_detail'),
    path('sg/ligues/<uuid:ligue_id>/transferer/', views_sg_ligues.sg_transferer_ligue_division, name='sg_transferer_ligue_division'),
    path('sg/ligues/<uuid:ligue_id>/approuver/', views_sg_ligues.sg_approuver_ligue, name='sg_approuver_ligue'),
    path('sg/ligues/<uuid:ligue_id>/rejeter/', views_sg_ligues.sg_rejeter_ligue, name='sg_rejeter_ligue'),
    
    # Division Provinciale - Gestion des Ligues Provinciales
    path('division/ligues/<uuid:validation_id>/', views_division_ligues.division_ligue_detail, name='division_ligue_detail'),
    path('division/ligues/<uuid:validation_id>/valider/', views_division_ligues.division_valider_ligue, name='division_valider_ligue'),
    path('division/ligues/<uuid:validation_id>/rejeter/', views_division_ligues.division_rejeter_ligue, name='division_rejeter_ligue'),
    
    # Secrétaire de Ligue Provinciale
    path('ligue/dashboard/', views_ligue_secretary.ligue_secretary_dashboard, name='ligue_secretary_dashboard'),
    path('ligue/clubs/', views_ligue_secretary.ligue_clubs_affiliation, name='ligue_clubs_list'),
    path('ligue/clubs/<uuid:club_id>/', views_ligue_secretary.ligue_club_detail, name='ligue_club_detail'),
    path('ligue/clubs/affiliation/', views_ligue_secretary.ligue_clubs_affiliation, name='ligue_clubs_affiliation'),
    path('ligue/clubs/<uuid:club_id>/affiliate/', views_ligue_secretary.ligue_club_affiliate, name='ligue_club_affiliate'),
    path('ligue/clubs/<uuid:club_id>/resend-activation/', views_ligue_secretary.ligue_club_resend_activation, name='ligue_club_resend_activation'),
    path('ligue/clubs/create/step1/', views_ligue_secretary.ligue_club_create_step1, name='ligue_club_create_step1'),
    path('ligue/clubs/create/step2/', views_ligue_secretary.ligue_club_create_step2, name='ligue_club_create_step2'),
    path('ligue/clubs/create/step3/', views_ligue_secretary.ligue_club_create_step3, name='ligue_club_create_step3'),
    path('ligue/profil/', views_ligue_secretary.ligue_profile, name='ligue_profile'),
    path('ligue/documents/', views_ligue_secretary.ligue_documents, name='ligue_documents'),
    path('ligue/communications/', views_ligue_secretary.ligue_communications, name='ligue_communications'),
    path('ligue/medecins/', views_ligue_secretary.ligue_medecins_list, name='ligue_medecins_list'),
    path('ligue/medecins/register/', views_ligue_secretary.ligue_medecin_register, name='ligue_medecin_register'),
    
    # Enrôlement des athlètes à la Ligue
    path('ligue/athletes/enrollment/', views_ligue_secretary.ligue_athletes_enrollment_list, name='ligue_athletes_enrollment_list'),
    path('ligue/athletes/<uuid:athlete_uid>/enroll/', views_ligue_secretary.ligue_athlete_enroll, name='ligue_athlete_enroll'),
    path('ligue/athletes/<uuid:athlete_uid>/enroll/capture/', views_ligue_secretary.ligue_athlete_capture_empreintes, name='ligue_athlete_capture_empreintes'),
    path('ligue/athletes/<uuid:athlete_uid>/enroll/capture/empreintes-templates/', views_ligue_secretary.ligue_athlete_capture_empreintes_templates, name='ligue_athlete_capture_empreintes_templates'),
    
    # Athlètes certifiés (ligue : voir les joueurs ayant réussi la certification)
    path('ligue/athletes/certifies/', views_ligue_secretary.ligue_athletes_certifies_list, name='ligue_athletes_certifies_list'),
    # Compétitions (types, compétitions par saison, calendrier)
    path('ligue/types-competition/', views_ligue_secretary.ligue_types_competition_list, name='ligue_types_competition_list'),
    path('ligue/competitions/', views_ligue_secretary.ligue_competitions_list, name='ligue_competitions_list'),
    path('ligue/competitions/create/', views_ligue_secretary.ligue_competition_create, name='ligue_competition_create'),
    path('ligue/competitions/<uuid:competition_uid>/calendrier/', views_ligue_secretary.ligue_competition_calendrier, name='ligue_competition_calendrier'),
    path('ligue/competitions/<uuid:competition_uid>/journees/', views_ligue_secretary.ligue_competition_journees, name='ligue_competition_journees'),
    path('ligue/competitions/<uuid:competition_uid>/journees/<uuid:journee_uid>/rencontre/create/', views_ligue_secretary.ligue_rencontre_create, name='ligue_rencontre_create'),
    path('ligue/rencontres/<uuid:rencontre_uid>/detail/', views_ligue_secretary.ligue_rencontre_detail, name='ligue_rencontre_detail'),
    path('ligue/rencontres/<uuid:rencontre_uid>/billetterie/', views_ligue_secretary.ligue_rencontre_billetterie_stats, name='ligue_rencontre_billetterie_stats'),
    path('ligue/competitions/<uuid:competition_uid>/rencontres/<uuid:rencontre_uid>/edit/', views_ligue_secretary.ligue_rencontre_edit, name='ligue_rencontre_edit'),
    path('ligue/calendrier-competition/', views_competitions.ligue_calendrier_competition, name='ligue_calendrier_competition'),
    path('ligue/competitions/<uuid:competition_uid>/calendrier-rencontres/', views_ligue_secretary.ligue_calendrier_rencontres, name='ligue_calendrier_rencontres'),
    path('ligue/competitions/<uuid:competition_uid>/calendrier-rencontres/api/', views_ligue_secretary.ligue_calendrier_rencontres_api, name='ligue_calendrier_rencontres_api'),
    path('ligue/rencontres/<uuid:rencontre_uid>/update/', views_ligue_secretary.ligue_rencontre_update_api, name='ligue_rencontre_update_api'),
    # Événements (matchs, galas ponctuels — séparé des compétitions)
    path('ligue/evenements/', views_ligue_secretary.ligue_evenements_list, name='ligue_evenements_list'),
    path('ligue/evenements/create/', views_ligue_secretary.ligue_evenement_create, name='ligue_evenement_create'),
    # Validation des athlètes par la Ligue
    path('ligue/athletes/validation/', views_ligue_secretary.ligue_athletes_validation_list, name='ligue_athletes_validation_list'),
    path('ligue/athletes/validation/historique/', views_ligue_secretary.ligue_athletes_validation_history, name='ligue_athletes_validation_history'),
    path('ligue/athletes/<uuid:athlete_uid>/validate/', views_ligue_secretary.ligue_athlete_validate, name='ligue_athlete_validate'),
    path('ligue/athletes/<uuid:athlete_uid>/verify-duplicates/', views_ligue_secretary.ligue_athlete_verify_duplicates, name='ligue_athlete_verify_duplicates'),
    # Historique des enrôlements
    path('ligue/athletes/enrollment/historique/', views_ligue_secretary.ligue_athletes_enrollment_history, name='ligue_athletes_enrollment_history'),
    
    # Club Validation by Provincial Director
    path('directeur-provincial/clubs-en-attente/', clubs_en_attente_validation, name='clubs_en_attente_validation'),
    path('directeur-provincial/clubs/<uuid:validation_id>/valider/', club_validation_detail, name='club_validation_detail'),
    # Division — Médecins des Ligues (liste des médecins enregistrés, création compte pour un médecin)
    path('division/medecins/', views_medecin_division.division_medecins_list, name='division_medecins_list'),
    path('division/medecins/<uuid:medecin_ligue_uid>/create-account/', views_medecin_division.division_medecin_create_account, name='division_medecin_create_account'),
    path('division/medecins/profil/<int:profil_id>/toggle/', views_medecin_division.division_medecin_toggle_actif, name='division_medecin_toggle_actif'),
    # Médecin Inspecteur — Dossiers médicaux des athlètes
    path('medecin/dashboard/', views_medecin_ligue.medecin_dashboard, name='medecin_dashboard'),
    path('medecin/athletes/en-attente-examen/', views_medecin_ligue.medecin_athletes_en_attente_examen, name='medecin_athletes_en_attente_examen'),
    path('medecin/athletes/<uuid:athlete_uid>/examen-medical/', views_medecin_ligue.medecin_athlete_examen_medical, name='medecin_athlete_examen_medical'),
    path('medecin/athletes/<uuid:athlete_uid>/examen-medical/empreinte-template/', views_medecin_ligue.medecin_athlete_empreinte_template, name='medecin_athlete_empreinte_template'),
    path('medecin/athletes/', views_medecin_ligue.medecin_athletes_list, name='medecin_athletes_list'),
    path('medecin/athletes/<uuid:athlete_uid>/dossier/', views_medecin_ligue.medecin_athlete_dossier, name='medecin_athlete_dossier'),
    # Médecin Inspecteur — Types d'examens (référentiel)
    path('medecin/types-examen/', views_medecin_ligue.medecin_types_examen_list, name='medecin_types_examen_list'),
    path('medecin/types-examen/create/', views_medecin_ligue.medecin_type_examen_create, name='medecin_type_examen_create'),
    path('medecin/types-examen/<int:type_examen_id>/edit/', views_medecin_ligue.medecin_type_examen_edit, name='medecin_type_examen_edit'),
    
    # Secrétaire du Club
    path('club/dashboard/', views_club_secretary.club_secretary_dashboard, name='club_secretary_dashboard'),
    path('club/identity/', views_club_secretary.club_identity, name='club_identity'),
    path('club/documents/', views_club_secretary.club_documents, name='club_documents'),
    path('club/athletes/', views_club_secretary.club_athletes_list, name='club_athletes_list'),
    path('club/licenses/', views_club_secretary.club_license_requests, name='club_license_requests'),
    path('club/licences-galerie/', views_club_secretary.club_licences_galerie, name='club_licences_galerie'),
    path('club/athlete-registration/', views_club_secretary.club_athlete_registration, name='club_athlete_registration'),
    path('club/athletes/<uuid:athlete_uid>/download-licence/', views_club_secretary.club_athlete_download_licence, name='club_athlete_download_licence'),
    path('club/athletes/<uuid:athlete_uid>/licence-print/', views_club_secretary.licence_f22_print, name='licence_f22_print'),
    path('club/staff/', views_club_secretary.club_staff, name='club_staff'),
    path('club/infrastructure/', views_club_secretary.club_infrastructure, name='club_infrastructure'),
    path('club/competitions/', views_club_secretary.club_competitions_calendar, name='club_competitions_calendar'),
    path('club/match-sheets/', views_club_secretary.club_match_sheets, name='club_match_sheets'),
]
