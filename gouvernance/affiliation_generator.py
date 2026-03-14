"""
Générateur d'Acte d'Affiliation Provincial pour les Clubs Sportifs.
Produit un document PDF officiel avec signature et sceau de la Ligue Provinciale.
"""
from datetime import datetime
from io import BytesIO
import os
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT, TA_LEFT
from reportlab.pdfgen import canvas
import qrcode
from PIL import Image as PILImage


def generer_numero_affiliation(ligue, annee=None):
    """
    Génère un numéro d'affiliation unique au format: A-YYYY-FÉDÉ-PROV-XXX
    A = Affiliation
    YYYY = Année
    FÉDÉ = Code de la fédération (3 premiers caractères du sigle)
    PROV = Province
    XXX = Numéro séquentiel
    """
    from gouvernance.models import Institution
    
    if annee is None:
        annee = datetime.now().year
    
    # Récupérer la fédération parente
    federation = ligue.institution_tutelle
    if not federation:
        federation_code = "XXX"
    else:
        federation_code = (federation.sigle or federation.code)[:3].upper()
    
    # Récupérer la province
    province_code = "PROV"
    if ligue.province_admin:
        province_code = (ligue.province_admin.designation or "PROV")[:4].upper()
    
    # Compter les affiliations déjà créées cette année pour cette ligue
    count = Institution.objects.filter(
        institution_tutelle=ligue,
        numero_affiliation__contains=f"A-{annee}",
        statut_validation_club='AFFILIEE'
    ).count()
    
    numero_seq = count + 1
    return f"A-{annee}-{federation_code}-{province_code}-{numero_seq:03d}"


def redimensionner_image(image_path, max_width_cm, max_height_cm):
    """
    Redimensionne une image pour qu'elle ne dépasse pas les dimensions max.
    Préserve le ratio d'aspect.
    Retourne un BytesIO avec l'image redimensionnée en PNG.
    """
    try:
        img = PILImage.open(image_path)
        
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        max_width_px = int(max_width_cm * 37.8)
        max_height_px = int(max_height_cm * 37.8)
        
        ratio = min(max_width_px / img.width, max_height_px / img.height)
        
        if ratio < 1:
            new_width = int(img.width * ratio)
            new_height = int(img.height * ratio)
            img = img.resize((new_width, new_height), PILImage.Resampling.LANCZOS)
        
        output = BytesIO()
        img.save(output, format='PNG')
        output.seek(0)
        
        return output
    except Exception as e:
        print(f"Erreur lors du redimensionnement de l'image: {e}")
        return None


def generer_qrcode_club(club_uid):
    """
    Génère un QR Code pointant vers la fiche publique du club.
    Format: https://sisep-sport.gouv.cd/club/{club_uid}/
    """
    try:
        # URL publique du club (à adapter selon votre domaine)
        base_url = getattr(settings, 'SISEP_PUBLIC_URL', 'https://sisep-sport.gouv.cd')
        club_url = f"{base_url}/club/{club_uid}/"
        
        # Générer le QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(club_url)
        qr.make(fit=True)
        
        # Créer une image PIL
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Sauvegarder en BytesIO
        output = BytesIO()
        qr_img.save(output, format='PNG')
        output.seek(0)
        
        return output
    except Exception as e:
        print(f"Erreur lors de la génération du QR Code: {e}")
        return None


def generer_acte_affiliation(club, ligue, validation_club):
    """
    Génère le PDF de l'Acte d'Affiliation Provincial pour un club.
    
    Args:
        club: Instance de Institution (le club)
        ligue: Instance de Institution (la ligue parente)
        validation_club: Instance de ClubValidation (contient l'avis technique)
    
    Returns:
        BytesIO: Le PDF généré
    """
    from gouvernance.models import Institution
    
    # Générer le numéro d'affiliation
    numero_affiliation = generer_numero_affiliation(ligue)
    
    # Créer le PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=2*cm,
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Style personnalisé pour le titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#0036ca'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    )
    
    # Style pour le sous-titre
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#0036ca'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    )
    
    # Style pour le corps
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=10,
        leading=14,
    )
    
    # Style pour les labels
    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#666666'),
        fontName='Helvetica-Bold',
        spaceAfter=3,
    )
    
    # Contenu du document
    elements = []
    
    # En-tête
    federation = ligue.institution_tutelle
    federation_name = federation.nom_officiel if federation else "FÉDÉRATION"
    discipline = "DISCIPLINE"  # À récupérer depuis les disciplines de la fédération
    province = ligue.province_admin.designation if ligue.province_admin else "PROVINCE"
    
    elements.append(Paragraph(
        f"FÉDÉRATION CONGOLAISE DE {discipline.upper()}",
        subtitle_style
    ))
    elements.append(Paragraph(
        f"LIGUE PROVINCIALE DU {province.upper()}",
        subtitle_style
    ))
    elements.append(Paragraph(
        "Affiliée au Ministère des Sports et Loisirs",
        label_style
    ))
    elements.append(Spacer(1, 0.5*cm))
    
    # Titre
    elements.append(Paragraph(
        "ACTE D'AFFILIATION SPORTIVE",
        title_style
    ))
    elements.append(Paragraph(
        f"N° : {numero_affiliation}",
        subtitle_style
    ))
    elements.append(Spacer(1, 0.5*cm))
    
    # Corps du texte
    elements.append(Paragraph(
        f"La Ligue Provinciale de {discipline} du {province}, après examen du dossier administratif et technique déposé par le groupement sportif ci-après ;",
        body_style
    ))
    
    # Avis technique
    if validation_club and validation_club.statut == 'ACCEPTEE':
        elements.append(Paragraph(
            f"VU l'Avis Technique Favorable de la Division Provinciale des Sports ;",
            body_style
        ))
    
    elements.append(Spacer(1, 0.3*cm))
    
    # Prononcé
    elements.append(Paragraph(
        "PRONONCE L'AFFILIATION DE :",
        ParagraphStyle(
            'Pronounce',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            spaceAfter=10,
        )
    ))
    
    elements.append(Spacer(1, 0.2*cm))
    
    # Détails du club
    club_details = [
        ("NOM DU CLUB :", club.nom_officiel),
        ("SIGLE :", club.sigle or "—"),
        ("CODE :", club.code or "—"),
        ("SIÈGE SOCIAL :", club.email_officiel or "—"),
        ("PRÉSIDENT :", club.nom_president or "—"),
    ]
    
    for label, value in club_details:
        elements.append(Paragraph(
            f"<b>{label}</b> {value}",
            body_style
        ))
    
    elements.append(Spacer(1, 0.3*cm))
    
    # Engagement
    saison = datetime.now().year
    elements.append(Paragraph(
        f"Le club susmentionné est autorisé à participer aux compétitions officielles organisées sous l'égide de la Ligue et de la Fédération pour la saison {saison}.",
        body_style
    ))
    
    elements.append(Spacer(1, 0.2*cm))
    
    elements.append(Paragraph(
        "Il s'engage, par la présente affiliation, à respecter scrupuleusement les Statuts et Règlements de la Fédération ainsi que les lois de la République Démocratique du Congo relatives au sport.",
        body_style
    ))
    
    elements.append(Spacer(1, 0.5*cm))
    
    # QR Code
    qr_code = generer_qrcode_club(str(club.uid))
    if qr_code:
        qr_img = Image(qr_code, width=2*cm, height=2*cm)
        elements.append(qr_img)
        elements.append(Spacer(1, 0.2*cm))
        elements.append(Paragraph(
            "Scannez ce code pour vérifier le statut du club",
            ParagraphStyle(
                'QRLabel',
                parent=styles['Normal'],
                fontSize=8,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#666666'),
            )
        ))
    
    elements.append(Spacer(1, 0.5*cm))
    
    # Pied de page
    chef_lieu = ligue.province_admin.designation if ligue.province_admin else "PROVINCE"
    date_str = datetime.now().strftime("%d/%m/%Y")
    
    elements.append(Paragraph(
        f"Fait à {chef_lieu}, le {date_str}",
        ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            spaceAfter=20,
        )
    ))
    
    elements.append(Paragraph(
        "Pour la Ligue Provinciale,",
        ParagraphStyle(
            'FooterLabel',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            spaceAfter=30,
        )
    ))
    
    # Signature et cachet
    signature_added = False
    if ligue.signature_image:
        try:
            sig_img = redimensionner_image(ligue.signature_image.path, 3, 1.5)
            if sig_img:
                elements.append(Image(sig_img, width=3*cm, height=1.5*cm))
                signature_added = True
        except:
            pass
    
    if ligue.sceau_image:
        try:
            sceau_img = redimensionner_image(ligue.sceau_image.path, 2, 2)
            if sceau_img:
                elements.append(Image(sceau_img, width=2*cm, height=2*cm))
        except:
            pass
    
    if not signature_added:
        elements.append(Spacer(1, 1.5*cm))
    
    elements.append(Spacer(1, 0.3*cm))
    
    elements.append(Paragraph(
        f"<b>{ligue.nom_officiel}</b><br/>Le Secrétaire Provincial",
        ParagraphStyle(
            'Signatory',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
        )
    ))
    
    # Générer le PDF
    doc.build(elements)
    buffer.seek(0)
    
    return buffer, numero_affiliation
