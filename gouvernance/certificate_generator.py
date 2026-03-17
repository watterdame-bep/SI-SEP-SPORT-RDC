"""
Générateur de Certificat d'Homologation Nationale pour les Fédérations Sportives.
Format: A4 Portrait avec identité visuelle RDC.
"""
import io
import qrcode
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from PIL import Image, ImageDraw
from django.core.files.base import ContentFile


# Couleurs RDC
BLEU_ROYAL = HexColor('#0036ca')
JAUNE_DRAPEAU = HexColor('#FDE015')
ROUGE_DRAPEAU = HexColor('#ED1C24')
NOIR = HexColor('#000000')
GRIS_CLAIR = HexColor('#f8f9fa')


def generer_qr_code(url):
    """Génère un QR code et retourne une image PIL."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    return img


def creer_sceau_avec_fond_blanc(sceau_path, taille_cm=1.8):
    """
    Crée une image du sceau avec un fond blanc pour éviter le fond noir.
    
    Args:
        sceau_path: Chemin vers l'image du sceau
        taille_cm: Taille en centimètres
    
    Returns:
        Chemin temporaire du fichier PNG avec fond blanc
    """
    try:
        from PIL import Image
        import tempfile
        import os
        
        # Ouvrir l'image du sceau
        sceau = Image.open(sceau_path)
        
        # Convertir en RGBA si nécessaire
        if sceau.mode != 'RGBA':
            sceau = sceau.convert('RGBA')
        
        # Créer une image avec fond blanc
        taille_px = int(taille_cm * 28.35)  # Conversion cm to pixels (72 DPI)
        fond_blanc = Image.new('RGBA', (taille_px, taille_px), (255, 255, 255, 255))
        
        # Redimensionner le sceau
        sceau_redim = sceau.resize((taille_px, taille_px), Image.Resampling.LANCZOS)
        
        # Coller le sceau sur le fond blanc
        fond_blanc.paste(sceau_redim, (0, 0), sceau_redim)
        
        # Sauvegarder dans un fichier temporaire
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            fond_blanc.save(tmp_file.name, format='PNG')
            return tmp_file.name
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Erreur lors de la création du sceau avec fond blanc: {str(e)}")
        return sceau_path  # Retourner l'original en cas d'erreur


def creer_filigrane(largeur, hauteur):
    """Crée une image de filigrane avec le lion de la RDC (placeholder)."""
    filigrane = Image.new('RGBA', (int(largeur), int(hauteur)), (255, 255, 255, 0))
    draw = ImageDraw.Draw(filigrane)
    
    # Texte de filigrane centré
    texte = "SISEP"
    # Utiliser une taille de police approximative
    draw.text(
        (int(largeur/2), int(hauteur/2)),
        texte,
        fill=(0, 54, 202, 13),  # Bleu royal avec 5% opacité
        anchor="mm"
    )
    
    return filigrane


def generer_attestation_homologation_ligue(ligue, base_url=None):
    """
    Génère l'Attestation d'Homologation Provinciale en PDF.
    Document officiel généré par le Secrétaire Général lors de l'approbation d'une ligue provinciale.
    Format conforme aux normes administratives RDC.
    
    Args:
        ligue: Instance du modèle Institution (Ligue Provinciale)
        base_url: URL de base pour les QR codes (optionnel)
    
    Returns:
        ContentFile: Fichier PDF prêt à être sauvegardé
    """
    from django.conf import settings
    
    if base_url is None:
        base_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
    
    # Créer le buffer PDF
    buffer = io.BytesIO()
    
    # Initialiser le canvas
    c = canvas.Canvas(buffer, pagesize=A4)
    largeur, hauteur = A4
    
    # ===== BORDURES =====
    # Bordure externe (Bleu Royal 2pt)
    c.setLineWidth(2)
    c.setStrokeColor(BLEU_ROYAL)
    c.rect(0.7*cm, 0.7*cm, largeur - 1.4*cm, hauteur - 1.4*cm)
    
    # Liseré intérieur (Jaune 1pt)
    c.setLineWidth(1)
    c.setStrokeColor(JAUNE_DRAPEAU)
    c.rect(1*cm, 1*cm, largeur - 2*cm, hauteur - 2*cm)
    
    # ===== EN-TÊTE OFFICIEL =====
    y_pos = hauteur - 1.3*cm
    
    # Ajouter le sceau du ministère au centre en haut (au-dessus des bordures)
    try:
        sceau_path = 'media/sceaux/logo-rdc.png'
        # Créer une version du sceau avec fond blanc
        sceau_avec_fond = creer_sceau_avec_fond_blanc(sceau_path, taille_cm=1.8)
        
        # Positionner le sceau au-dessus de la bordure supérieure
        sceau_x = largeur/2 - 0.9*cm  # Centré horizontalement
        sceau_y = hauteur - 1.5*cm     # Légèrement au-dessus de la bordure
        
        c.drawImage(
            sceau_avec_fond,
            sceau_x,
            sceau_y,
            width=1.8*cm,
            height=1.8*cm,
            preserveAspectRatio=True
        )
        
        # Nettoyer le fichier temporaire
        import os
        try:
            os.unlink(sceau_avec_fond)
        except:
            pass
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Impossible d'insérer le sceau du ministère: {str(e)}")
    
    y_pos -= 1.5*cm  # Décaler le texte vers le bas pour faire place au sceau
    
    # Texte en-tête
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(NOIR)
    c.drawCentredString(largeur/2, y_pos, "RÉPUBLIQUE DÉMOCRATIQUE DU CONGO")
    
    y_pos -= 0.5*cm
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(BLEU_ROYAL)
    c.drawCentredString(largeur/2, y_pos, "MINISTÈRE DES SPORTS ET LOISIRS")
    
    y_pos -= 0.5*cm
    c.setFont("Helvetica", 10)
    c.setFillColor(NOIR)
    c.drawCentredString(largeur/2, y_pos, "Secrétariat Général aux Sports")
    
    y_pos -= 0.8*cm
    
    # ===== TITRE PRINCIPAL =====
    c.setFont("Helvetica-Bold", 15)
    c.setFillColor(BLEU_ROYAL)
    c.drawCentredString(largeur/2, y_pos, "ATTESTATION D'HOMOLOGATION PROVINCIALE")
    
    y_pos -= 0.6*cm
    
    # ===== NUMÉRO D'ATTESTATION =====
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(ROUGE_DRAPEAU)
    from gouvernance.models import AttestationReconnaissance
    attestation = AttestationReconnaissance.objects.filter(ligue=ligue).first()
    numero_attestation = attestation.numero_attestation if attestation else "EN ATTENTE"
    c.drawCentredString(largeur/2, y_pos, f"N° {numero_attestation}")
    
    y_pos -= 1*cm
    
    # ===== CORPS DU TEXTE - INTRODUCTION =====
    c.setFont("Helvetica", 10)
    c.setFillColor(NOIR)
    
    # Texte introductif
    texte_intro = "Le Secrétaire Général aux Sports et Loisirs, agissant dans le cadre de ses"
    c.drawCentredString(largeur/2, y_pos, texte_intro)
    
    y_pos -= 0.4*cm
    texte_intro2 = "compétences techniques et par délégation de pouvoir ;"
    c.drawCentredString(largeur/2, y_pos, texte_intro2)
    
    y_pos -= 0.7*cm
    
    # ===== CLAUSES VU =====
    c.setFont("Helvetica", 9.5)
    
    # VU 1
    texte_vu1 = "VU la Loi n°11/023 du 24 décembre 2011 portant principes fondamentaux"
    c.drawString(1.5*cm, y_pos, texte_vu1)
    y_pos -= 0.35*cm
    texte_vu1b = "relatifs à l'organisation et à la promotion des activités physiques et sportives"
    c.drawString(1.5*cm, y_pos, texte_vu1b)
    y_pos -= 0.35*cm
    texte_vu1c = "en République Démocratique du Congo ;"
    c.drawString(1.5*cm, y_pos, texte_vu1c)
    
    y_pos -= 0.5*cm
    
    # VU 2 - Arrêté de la Fédération
    federation = ligue.institution_tutelle
    federation_name = federation.nom_officiel if federation else "Fédération"
    texte_vu2 = f"VU l'Arrêté Ministériel portant agrément de la Fédération : {federation_name} ;"
    c.drawString(1.5*cm, y_pos, texte_vu2)
    
    y_pos -= 0.5*cm
    
    # VU 3 - Rapport de viabilité
    province = ligue.province_admin.designation if ligue.province_admin else "Province"
    texte_vu3 = f"VU le rapport de viabilité favorable transmis par la Division Provinciale"
    c.drawString(1.5*cm, y_pos, texte_vu3)
    y_pos -= 0.35*cm
    texte_vu3b = f"des Sports du {province} ;"
    c.drawString(1.5*cm, y_pos, texte_vu3b)
    
    y_pos -= 0.7*cm
    
    # ===== ATTESTE PAR LA PRÉSENTE =====
    c.setFont("Helvetica-Bold", 10)
    c.drawString(1.5*cm, y_pos, "ATTESTE PAR LA PRÉSENTE :")
    
    y_pos -= 0.6*cm
    
    # ===== CORPS PRINCIPAL =====
    c.setFont("Helvetica", 10)
    
    texte_principal = "Que la structure sportive dénommée :"
    c.drawString(1.5*cm, y_pos, texte_principal)
    
    y_pos -= 0.5*cm
    
    # Nom de la ligue en gras
    c.setFont("Helvetica-Bold", 10)
    disciplines = ", ".join([d.designation for d in ligue.disciplines.all()])
    if disciplines:
        nom_ligue = f"LIGUE PROVINCIALE DE {disciplines.upper()} DU {province.upper()}"
    else:
        nom_ligue = f"LIGUE PROVINCIALE DU {province.upper()}"
    
    # Centrer le nom de la ligue
    c.drawCentredString(largeur/2, y_pos, nom_ligue)
    
    y_pos -= 0.6*cm
    
    # Texte de reconnaissance
    c.setFont("Helvetica", 10)
    texte_reconnaissance = "est officiellement homologuée pour exercer ses activités sur toute l'étendue"
    c.drawString(1.5*cm, y_pos, texte_reconnaissance)
    y_pos -= 0.35*cm
    texte_reconnaissance2 = "de ladite province."
    c.drawString(1.5*cm, y_pos, texte_reconnaissance2)
    
    y_pos -= 0.6*cm
    
    # ===== BUREAU EXÉCUTIF =====
    c.setFont("Helvetica-Bold", 10)
    c.drawString(1.5*cm, y_pos, "Les membres du Bureau Exécutif dûment reconnus sont :")
    
    y_pos -= 0.5*cm
    
    c.setFont("Helvetica", 10)
    # Récupérer les dirigeants de la ligue via les membres
    membres = ligue.membres.all()
    
    if membres.exists():
        for membre in membres[:2]:  # Afficher les 2 premiers membres
            fonction = membre.fonction.designation if membre.fonction else "Fonction"
            nom = membre.personne.nom_complet if membre.personne else "Non renseigné"
            c.drawString(2*cm, y_pos, f"• {fonction} : {nom}")
            y_pos -= 0.35*cm
    else:
        c.drawString(2*cm, y_pos, "• Président : À désigner")
        y_pos -= 0.35*cm
        c.drawString(2*cm, y_pos, "• Secrétaire Provincial : À désigner")
        y_pos -= 0.35*cm
    
    y_pos -= 0.4*cm
    
    # ===== VALIDITÉ =====
    c.setFont("Helvetica", 10)
    annee_saison = datetime.now().year
    texte_validite = f"Cette homologation est valable pour la saison sportive {annee_saison} et est soumise au"
    c.drawString(1.5*cm, y_pos, texte_validite)
    y_pos -= 0.35*cm
    texte_validite2 = "respect des règlements généraux de sa Fédération de tutelle et des directives du"
    c.drawString(1.5*cm, y_pos, texte_validite2)
    y_pos -= 0.35*cm
    texte_validite3 = "Secrétariat Général."
    c.drawString(1.5*cm, y_pos, texte_validite3)
    
    y_pos -= 0.8*cm
    
    # ===== QR CODE (bas gauche) =====
    qr_url = f"{base_url}/gouvernance/verifier-ligue/{ligue.uid}/"
    qr_img = generer_qr_code(qr_url)
    
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        qr_img.save(tmp_file.name, format='PNG')
        qr_path = tmp_file.name
    
    qr_x = 1.5*cm
    qr_y = y_pos - 2.2*cm
    try:
        c.drawImage(qr_path, qr_x, qr_y, width=1.8*cm, height=1.8*cm)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Impossible d'insérer le QR code: {str(e)}")
    finally:
        import os
        try:
            os.unlink(qr_path)
        except:
            pass
    
    # Label QR
    c.setFont("Helvetica", 7)
    c.setFillColor(GRIS_CLAIR)
    c.drawString(qr_x, qr_y - 0.35*cm, "Vérifier")
    
    # ===== SIGNATURE (bas droit) =====
    sig_x = largeur - 4.5*cm
    sig_y = y_pos - 0.3*cm
    
    c.setFont("Helvetica", 9)
    c.setFillColor(NOIR)
    
    # Date et lieu
    date_jour = datetime.now().strftime("%d/%m/%Y")
    c.drawString(sig_x, sig_y, f"Fait à Kinshasa, le {date_jour}")
    
    sig_y -= 0.7*cm
    
    # Titre
    c.setFont("Helvetica-Bold", 9)
    c.drawString(sig_x, sig_y, "Le Secrétaire Général aux Sports")
    
    sig_y -= 0.35*cm
    c.setFont("Helvetica", 8)
    c.drawString(sig_x, sig_y, "et Loisirs,")
    
    sig_y -= 1*cm
    
    # Charger le cachet du SG depuis le profil
    try:
        from core.models import ProfilUtilisateur
        sg_profil = ProfilUtilisateur.objects.filter(role='INSTITUTION_ADMIN').first()
        
        if sg_profil and sg_profil.sceau_image:
            # Afficher le cachet du SG
            cachet_x = sig_x + 0.3*cm
            cachet_y = sig_y - 1.2*cm
            try:
                c.drawImage(
                    sg_profil.sceau_image.path,
                    cachet_x,
                    cachet_y,
                    width=1.5*cm,
                    height=1.5*cm
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Impossible d'insérer le cachet du SG: {str(e)}")
            
            sig_y -= 1.8*cm
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Erreur lors du chargement du cachet du SG: {str(e)}")
    
    # Espace pour signature
    c.setLineWidth(1)
    c.setStrokeColor(NOIR)
    c.line(sig_x, sig_y, sig_x + 2.5*cm, sig_y)
    
    sig_y -= 0.3*cm
    c.setFont("Helvetica", 8)
    c.drawString(sig_x + 0.3*cm, sig_y, "Signature & Cachet")
    
    # ===== PIED DE PAGE =====
    c.setFont("Helvetica", 7)
    c.setFillColor(GRIS_CLAIR)
    c.drawString(1.5*cm, 0.7*cm, f"Attestation générée le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
    c.drawRightString(largeur - 1.5*cm, 0.7*cm, f"Numéro: {numero_attestation}")
    
    # Finaliser le PDF
    c.save()
    
    # Retourner le contenu
    buffer.seek(0)
    return ContentFile(buffer.getvalue(), name=f"Attestation_Homologation_Ligue_{numero_attestation}.pdf")


def generer_certificat_homologation(institution, base_url=None):
    """
    Génère le Certificat d'Homologation Nationale en PDF.
    Document officiel généré par le Ministre lors de l'homologation d'une institution.
    Format conforme aux normes administratives RDC.
    
    Args:
        institution: Instance du modèle Institution
        base_url: URL de base pour les QR codes (optionnel)
    
    Returns:
        ContentFile: Fichier PDF prêt à être sauvegardé
    """
    from django.conf import settings
    
    if base_url is None:
        base_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
    
    # Créer le buffer PDF
    buffer = io.BytesIO()
    
    # Initialiser le canvas
    c = canvas.Canvas(buffer, pagesize=A4)
    largeur, hauteur = A4
    
    # ===== BORDURES =====
    # Bordure externe (Bleu Royal 2pt)
    c.setLineWidth(2)
    c.setStrokeColor(BLEU_ROYAL)
    c.rect(0.7*cm, 0.7*cm, largeur - 1.4*cm, hauteur - 1.4*cm)
    
    # Liseré intérieur (Jaune 1pt)
    c.setLineWidth(1)
    c.setStrokeColor(JAUNE_DRAPEAU)
    c.rect(1*cm, 1*cm, largeur - 2*cm, hauteur - 2*cm)
    
    # ===== EN-TÊTE OFFICIEL =====
    y_pos = hauteur - 1.3*cm
    
    # Ajouter le sceau du ministère au centre en haut
    try:
        sceau_path = 'media/sceaux/logo-rdc.png'
        # Créer une version du sceau avec fond blanc
        sceau_avec_fond = creer_sceau_avec_fond_blanc(sceau_path, taille_cm=1.8)
        
        # Positionner le sceau au-dessus de la bordure supérieure
        sceau_x = largeur/2 - 0.9*cm  # Centré horizontalement
        sceau_y = hauteur - 1.5*cm     # Légèrement au-dessus de la bordure
        
        c.drawImage(
            sceau_avec_fond,
            sceau_x,
            sceau_y,
            width=1.8*cm,
            height=1.8*cm,
            preserveAspectRatio=True
        )
        
        # Nettoyer le fichier temporaire
        import os
        try:
            os.unlink(sceau_avec_fond)
        except:
            pass
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Impossible d'insérer le sceau du ministère: {str(e)}")
    
    y_pos -= 1.5*cm  # Décaler le texte vers le bas pour faire place au sceau
    
    # Texte en-tête
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(NOIR)
    c.drawCentredString(largeur/2, y_pos, "RÉPUBLIQUE DÉMOCRATIQUE DU CONGO")
    
    y_pos -= 0.5*cm
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(BLEU_ROYAL)
    c.drawCentredString(largeur/2, y_pos, "MINISTÈRE DES SPORTS ET LOISIRS")
    
    y_pos -= 0.5*cm
    c.setFont("Helvetica", 10)
    c.setFillColor(NOIR)
    c.drawCentredString(largeur/2, y_pos, "Cabinet du Ministre")
    
    y_pos -= 0.8*cm
    
    # ===== TITRE PRINCIPAL =====
    c.setFont("Helvetica-Bold", 15)
    c.setFillColor(BLEU_ROYAL)
    c.drawCentredString(largeur/2, y_pos, "CERTIFICAT D'HOMOLOGATION NATIONALE")
    
    y_pos -= 0.6*cm
    
    # ===== NUMÉRO D'HOMOLOGATION =====
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(ROUGE_DRAPEAU)
    numero_homologation = institution.numero_homologation if institution.numero_homologation else "EN ATTENTE"
    c.drawCentredString(largeur/2, y_pos, f"N° {numero_homologation}")
    
    y_pos -= 1*cm
    
    # ===== CORPS DU TEXTE - INTRODUCTION =====
    c.setFont("Helvetica", 10)
    c.setFillColor(NOIR)
    
    # Texte introductif
    texte_intro = "Le Ministre des Sports et Loisirs, agissant au nom du Gouvernement,"
    c.drawCentredString(largeur/2, y_pos, texte_intro)
    
    y_pos -= 0.4*cm
    texte_intro2 = "Vu les textes législatifs et réglementaires en vigueur,"
    c.drawCentredString(largeur/2, y_pos, texte_intro2)
    
    y_pos -= 0.7*cm
    
    # ===== CLAUSES VU =====
    c.setFont("Helvetica", 9.5)
    
    # VU 1
    texte_vu1 = "VU la Loi n°11/023 du 24 décembre 2011 portant principes fondamentaux"
    c.drawString(1.5*cm, y_pos, texte_vu1)
    y_pos -= 0.35*cm
    texte_vu1b = "relatifs à l'organisation et à la promotion des activités physiques et sportives"
    c.drawString(1.5*cm, y_pos, texte_vu1b)
    y_pos -= 0.35*cm
    texte_vu1c = "en République Démocratique du Congo ;"
    c.drawString(1.5*cm, y_pos, texte_vu1c)
    
    y_pos -= 0.5*cm
    
    # VU 2 - Rapport de viabilité
    texte_vu2 = "VU le rapport de viabilité favorable transmis par le Secrétariat Général aux Sports ;"
    c.drawString(1.5*cm, y_pos, texte_vu2)
    
    y_pos -= 0.5*cm
    
    # VU 3 - Procédure régulière
    texte_vu3 = "VU que la procédure d'homologation a été régulièrement suivie ;"
    c.drawString(1.5*cm, y_pos, texte_vu3)
    
    y_pos -= 0.7*cm
    
    # ===== CERTIFIE PAR LA PRÉSENTE =====
    c.setFont("Helvetica-Bold", 10)
    c.drawString(1.5*cm, y_pos, "CERTIFIE PAR LA PRÉSENTE :")
    
    y_pos -= 0.6*cm
    
    # ===== CORPS PRINCIPAL =====
    c.setFont("Helvetica", 10)
    
    texte_principal = "Que l'institution sportive dénommée :"
    c.drawString(1.5*cm, y_pos, texte_principal)
    
    y_pos -= 0.5*cm
    
    # Nom de l'institution en gras
    c.setFont("Helvetica-Bold", 10)
    nom_institution = institution.nom_officiel.upper()
    
    # Centrer le nom de l'institution
    c.drawCentredString(largeur/2, y_pos, nom_institution)
    
    y_pos -= 0.6*cm
    
    # Type d'institution
    c.setFont("Helvetica", 10)
    type_institution = institution.type_institution.designation if institution.type_institution else "INSTITUTION SPORTIVE"
    texte_type = f"Dûment reconnue comme {type_institution} nationale,"
    c.drawString(1.5*cm, y_pos, texte_type)
    
    y_pos -= 0.35*cm
    texte_type2 = "est officiellement homologuée pour exercer ses activités sur toute l'étendue"
    c.drawString(1.5*cm, y_pos, texte_type2)
    y_pos -= 0.35*cm
    texte_type3 = "du territoire national de la République Démocratique du Congo."
    c.drawString(1.5*cm, y_pos, texte_type3)
    
    y_pos -= 0.6*cm
    
    # ===== SIÈGE SOCIAL =====
    c.setFont("Helvetica-Bold", 10)
    c.drawString(1.5*cm, y_pos, "Siège social :")
    
    y_pos -= 0.4*cm
    c.setFont("Helvetica", 10)
    
    # Construire l'adresse avec les champs disponibles dans Institution
    siege_parts = []
    
    # Le modèle Institution n'a pas les champs adresse, on utilise une valeur par défaut
    # ou on pourrait ajouter ces champs si nécessaire
    if hasattr(institution, 'adresse_complete') and institution.adresse_complete:
        siege_parts.append(institution.adresse_complete)
    else:
        # Siège par défaut ou à préciser
        siege_parts.append("À préciser par l'institution")
    
    # Ajouter la province si disponible
    if institution.province_admin:
        siege_parts.append(institution.province_admin.designation)
    
    siege = ", ".join([part for part in siege_parts if part])
    c.drawString(2*cm, y_pos, siege)
    
    y_pos -= 0.6*cm
    
    # ===== BUREAU EXÉCUTIF =====
    c.setFont("Helvetica-Bold", 10)
    c.drawString(1.5*cm, y_pos, "Les membres du Bureau Exécutif dûment reconnus sont :")
    
    y_pos -= 0.5*cm
    
    c.setFont("Helvetica", 10)
    # Récupérer les dirigeants de l'institution via les membres
    membres = institution.membres.all()
    
    if membres.exists():
        for membre in membres[:3]:  # Afficher les 3 premiers membres
            fonction = membre.fonction.designation if membre.fonction else "Fonction"
            nom = membre.personne.nom_complet if membre.personne else "Non renseigné"
            c.drawString(2*cm, y_pos, f"• {fonction} : {nom}")
            y_pos -= 0.35*cm
    else:
        c.drawString(2*cm, y_pos, "• Président : À désigner")
        y_pos -= 0.35*cm
        c.drawString(2*cm, y_pos, "• Secrétaire Général : À désigner")
        y_pos -= 0.35*cm
        c.drawString(2*cm, y_pos, "• Trésorier : À désigner")
        y_pos -= 0.35*cm
    
    y_pos -= 0.4*cm
    
    # ===== VALIDITÉ =====
    c.setFont("Helvetica", 10)
    annee_saison = datetime.now().year
    texte_validite = f"Cette homologation est valable pour la saison sportive {annee_saison} et est soumise au"
    c.drawString(1.5*cm, y_pos, texte_validite)
    y_pos -= 0.35*cm
    texte_validite2 = "respect des règlements généraux et des directives du Ministère des Sports et Loisirs."
    c.drawString(1.5*cm, y_pos, texte_validite2)
    
    y_pos -= 0.8*cm
    
    # ===== QR CODE (bas gauche) =====
    qr_url = f"{base_url}/gouvernance/verifier-institution/{institution.uid}/"
    qr_img = generer_qr_code(qr_url)
    
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        qr_img.save(tmp_file.name, format='PNG')
        qr_path = tmp_file.name
    
    qr_x = 1.5*cm
    qr_y = y_pos - 2.2*cm
    try:
        c.drawImage(qr_path, qr_x, qr_y, width=1.8*cm, height=1.8*cm)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Impossible d'insérer le QR code: {str(e)}")
    finally:
        import os
        try:
            os.unlink(qr_path)
        except:
            pass
    
    # Label QR
    c.setFont("Helvetica", 7)
    c.setFillColor(GRIS_CLAIR)
    c.drawString(qr_x, qr_y - 0.35*cm, "Vérifier")
    
    # ===== SIGNATURE (bas droit) =====
    sig_x = largeur - 4.5*cm
    sig_y = y_pos - 0.3*cm
    
    c.setFont("Helvetica", 9)
    c.setFillColor(NOIR)
    
    # Date et lieu
    date_jour = datetime.now().strftime("%d/%m/%Y")
    c.drawString(sig_x, sig_y, f"Fait à Kinshasa, le {date_jour}")
    
    sig_y -= 0.7*cm
    
    # Titre
    c.setFont("Helvetica-Bold", 9)
    c.drawString(sig_x, sig_y, "Le Ministre des Sports")
    
    sig_y -= 0.35*cm
    c.setFont("Helvetica", 8)
    c.drawString(sig_x, sig_y, "et Loisirs,")
    
    sig_y -= 1*cm
    
    # Charger le cachet du Ministre depuis le profil
    try:
        from core.models import ProfilUtilisateur
        ministre_profil = ProfilUtilisateur.objects.filter(role='MINISTERE').first()
        
        if ministre_profil and ministre_profil.sceau_image:
            # Afficher le cachet du Ministre
            cachet_x = sig_x + 0.3*cm
            cachet_y = sig_y - 1.2*cm
            try:
                c.drawImage(
                    ministre_profil.sceau_image.path,
                    cachet_x,
                    cachet_y,
                    width=1.5*cm,
                    height=1.5*cm
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Impossible d'insérer le cachet du Ministre: {str(e)}")
            
            sig_y -= 1.8*cm
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Erreur lors du chargement du cachet du Ministre: {str(e)}")
    
    # Espace pour signature
    c.setLineWidth(1)
    c.setStrokeColor(NOIR)
    c.line(sig_x, sig_y, sig_x + 2.5*cm, sig_y)
    
    sig_y -= 0.3*cm
    c.setFont("Helvetica", 8)
    c.drawString(sig_x + 0.3*cm, sig_y, "Signature & Cachet")
    
    # ===== PIED DE PAGE =====
    c.setFont("Helvetica", 7)
    c.setFillColor(GRIS_CLAIR)
    c.drawString(1.5*cm, 0.7*cm, f"Certificat généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
    c.drawRightString(largeur - 1.5*cm, 0.7*cm, f"Numéro: {numero_homologation}")
    
    # Finaliser le PDF
    c.save()
    
    # Retourner le contenu
    buffer.seek(0)
    return ContentFile(buffer.getvalue(), name=f"Certificat_Homologation_{numero_homologation}.pdf")
