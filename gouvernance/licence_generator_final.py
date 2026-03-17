"""
Générateur de Licence Sportive - Version finale
Dessine directement sur les templates recto.png et verso.png
"""
import io
import os
import tempfile
import qrcode
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdf_canvas
from django.core.files.base import ContentFile
from django.conf import settings


# Format ID-1 en pixels à 300 DPI
ID1_WIDTH_PX = 1011  # 85.6mm * 300/25.4
ID1_HEIGHT_PX = 638  # 53.98mm * 300/25.4

# Format ID-1 en mm pour ReportLab
ID1_WIDTH_MM = 85.6
ID1_HEIGHT_MM = 53.98


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


def generer_licence_sportive_id1(athlete, base_url=None):
    """
    Génère la Licence Sportive Nationale au format ID-1.
    Dessine les informations directement sur les templates recto.png et verso.png.
    
    Returns:
        ContentFile: Fichier PDF prêt à être sauvegardé
    """
    if base_url is None:
        base_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
    base_url = base_url.rstrip('/')
    
    base_dir = settings.BASE_DIR
    
    # Chemins des templates
    recto_template = os.path.join(base_dir, 'licence_fichier', 'recto.png')
    verso_template = os.path.join(base_dir, 'licence_fichier', 'verso.png')
    
    # Créer les images recto et verso
    recto_img = _creer_recto(athlete, recto_template, base_url)
    verso_img = _creer_verso(athlete, verso_template)
    
    # Sauvegarder temporairement les images
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_recto:
        recto_img.save(tmp_recto.name, format='PNG', dpi=(300, 300))
        recto_path = tmp_recto.name
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_verso:
        verso_img.save(tmp_verso.name, format='PNG', dpi=(300, 300))
        verso_path = tmp_verso.name
    
    try:
        # Créer le PDF
        buffer = io.BytesIO()
        c = pdf_canvas.Canvas(buffer, pagesize=(ID1_WIDTH_MM * mm, ID1_HEIGHT_MM * mm))
        
        # Page 1: Recto
        c.drawImage(recto_path, 0, 0, width=ID1_WIDTH_MM * mm, height=ID1_HEIGHT_MM * mm)
        c.showPage()
        
        # Page 2: Verso
        c.drawImage(verso_path, 0, 0, width=ID1_WIDTH_MM * mm, height=ID1_HEIGHT_MM * mm)
        
        c.save()
        buffer.seek(0)
        
        numero_fichier = athlete.numero_licence or athlete.numero_sportif or str(athlete.uid)[:8]
        return ContentFile(buffer.getvalue(), name=f"Licence_ID1_{numero_fichier}.pdf")
        
    finally:
        # Nettoyer les fichiers temporaires
        try:
            os.unlink(recto_path)
            os.unlink(verso_path)
        except:
            pass


def _creer_recto(athlete, template_path, base_url):
    """
    Crée l'image recto en dessinant sur le template.
    Positions ajustées: informations très bas, QR code en bas à droite.
    """
    # Charger le template
    if os.path.exists(template_path):
        img = Image.open(template_path).convert('RGBA')
    else:
        img = Image.new('RGBA', (ID1_WIDTH_PX, ID1_HEIGHT_PX), (255, 255, 255, 255))
    
    draw = ImageDraw.Draw(img)
    
    # Charger les polices
    try:
        font_label = ImageFont.truetype("arialbd.ttf", 16)
        font_value = ImageFont.truetype("arial.ttf", 22)
    except:
        font_label = ImageFont.load_default()
        font_value = ImageFont.load_default()
    
    # Convertir mm en pixels (300 DPI)
    def mm_to_px(mm_val):
        return int(mm_val * 300 / 25.4)
    
    # === PHOTO DE L'ATHLÈTE ===
    photo_x = mm_to_px(15)
    photo_y = mm_to_px(35)
    photo_w = mm_to_px(18)
    photo_h = mm_to_px(22)
    
    if athlete.personne and athlete.personne.photo:
        try:
            photo = Image.open(athlete.personne.photo.path).convert('RGBA')
            photo = photo.resize((photo_w, photo_h), Image.Resampling.LANCZOS)
            img.paste(photo, (photo_x, photo_y), photo)
        except Exception as e:
            print(f"Erreur photo: {e}")
    
    # === INFORMATIONS - DESCENDRE BEAUCOUP PLUS BAS ===
    # Commencer à 30mm du haut au lieu de 22mm
    info_x = mm_to_px(25)
    info_y = mm_to_px(40)  # DESCENDU DE 22mm À 30mm
    line_spacing = mm_to_px(1.2)
    label_value_spacing = mm_to_px(2)
    
    # NOM
    draw.text((info_x, info_y), "NOM", fill=(0, 86, 179, 255), font=font_label)
    info_y += label_value_spacing
    nom = athlete.personne.nom.upper() if athlete.personne and athlete.personne.nom else ''
    draw.text((info_x, info_y), nom, fill=(0, 0, 0, 255), font=font_value)
    info_y += mm_to_px(3) + line_spacing
    
    # POST-NOM
    draw.text((info_x, info_y), "POST-NOM", fill=(0, 86, 179, 255), font=font_label)
    info_y += label_value_spacing
    postnom = athlete.personne.postnom.upper() if athlete.personne and athlete.personne.postnom else ''
    draw.text((info_x, info_y), postnom, fill=(0, 0, 0, 255), font=font_value)
    info_y += mm_to_px(3) + line_spacing
    
    # PRÉNOM
    draw.text((info_x, info_y), "PRÉNOM", fill=(0, 86, 179, 255), font=font_label)
    info_y += label_value_spacing
    prenom = athlete.personne.prenom.upper() if athlete.personne and athlete.personne.prenom else ''
    draw.text((info_x, info_y), prenom, fill=(0, 0, 0, 255), font=font_value)
    info_y += mm_to_px(3) + line_spacing
    
    # NÉ(E) LE
    draw.text((info_x, info_y), "NÉ(E) LE", fill=(0, 86, 179, 255), font=font_label)
    info_y += label_value_spacing
    date_naissance = ''
    if athlete.personne and athlete.personne.date_naissance:
        date_naissance = athlete.personne.date_naissance.strftime('%d/%m/%Y')
    draw.text((info_x, info_y), date_naissance, fill=(0, 0, 0, 255), font=font_value)
    info_y += mm_to_px(3) + line_spacing
    
    # DISCIPLINE
    draw.text((info_x, info_y), "DISCIPLINE", fill=(0, 86, 179, 255), font=font_label)
    info_y += label_value_spacing
    discipline = athlete.discipline.designation if athlete.discipline else ''
    draw.text((info_x, info_y), discipline, fill=(0, 86, 179, 255), font=font_value)
    
    # === QR CODE EN BAS À DROITE ===
    qr_url = f"{base_url}/gouvernance/verifier-athlete/{athlete.uid}/"
    qr_img = generer_qr_code(qr_url)
    qr_size = mm_to_px(15)  # 15mm de taille
    qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
    
    # Position: BAS À DROITE avec marge de 5mm
    qr_x = ID1_WIDTH_PX - qr_size - mm_to_px(5)  # À DROITE
    qr_y = ID1_HEIGHT_PX - qr_size - mm_to_px(5)  # EN BAS (marge de 5mm)
    img.paste(qr_img, (qr_x, qr_y))
    
    return img


def _creer_verso(athlete, template_path):
    """
    Crée l'image verso en dessinant sur le template.
    """
    # Charger le template
    if os.path.exists(template_path):
        img = Image.open(template_path).convert('RGBA')
    else:
        img = Image.new('RGBA', (ID1_WIDTH_PX, ID1_HEIGHT_PX), (255, 255, 255, 255))
    
    draw = ImageDraw.Draw(img)
    
    # Charger les polices
    try:
        font_label = ImageFont.truetype("arialbd.ttf", 20)
        font_value = ImageFont.truetype("arial.ttf", 26)
        font_small = ImageFont.truetype("arial.ttf", 18)
    except:
        font_label = ImageFont.load_default()
        font_value = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Convertir mm en pixels
    def mm_to_px(mm_val):
        return int(mm_val * 300 / 25.4)
    
    # === INFORMATIONS VERSO ===
    info_x = mm_to_px(10)
    info_y = mm_to_px(15)
    line_spacing = mm_to_px(2.5)
    
    # PROVINCE
    draw.text((info_x, info_y), "PROVINCE", fill=(0, 86, 179, 255), font=font_label)
    info_y += mm_to_px(3.5)
    province = ''
    if athlete.club and athlete.club.institution_tutelle:
        province = athlete.club.institution_tutelle.nom_officiel
    draw.text((info_x, info_y), province, fill=(0, 0, 0, 255), font=font_value)
    info_y += mm_to_px(4) + line_spacing
    
    # LIEU DE NAISSANCE
    draw.text((info_x, info_y), "LIEU DE NAISSANCE", fill=(0, 86, 179, 255), font=font_label)
    info_y += mm_to_px(3.5)
    lieu = ''
    if athlete.personne and athlete.personne.lieu_naissance:
        lieu = athlete.personne.lieu_naissance
    draw.text((info_x, info_y), lieu, fill=(0, 0, 0, 255), font=font_value)
    info_y += mm_to_px(4) + line_spacing
    
    # CLUB
    draw.text((info_x, info_y), "CLUB", fill=(0, 86, 179, 255), font=font_label)
    info_y += mm_to_px(3.5)
    club = athlete.club.nom_officiel if athlete.club else ''
    draw.text((info_x, info_y), club, fill=(0, 0, 0, 255), font=font_value)
    info_y += mm_to_px(4) + line_spacing
    
    # GROUPE SANGUIN
    draw.text((info_x, info_y), "GROUPE SANGUIN", fill=(0, 86, 179, 255), font=font_label)
    info_y += mm_to_px(3.5)
    groupe = athlete.groupe_sanguin if athlete.groupe_sanguin else 'N/A'
    draw.text((info_x, info_y), groupe, fill=(237, 28, 36, 255), font=font_value)
    
    # === TEXTE DE SÉCURITÉ EN BAS ===
    security_text = "Document officiel - Toute falsification est passible de sanctions"
    text_y = ID1_HEIGHT_PX - mm_to_px(5)
    # Centrer le texte
    bbox = draw.textbbox((0, 0), security_text, font=font_small)
    text_width = bbox[2] - bbox[0]
    text_x = (ID1_WIDTH_PX - text_width) // 2
    draw.text((text_x, text_y), security_text, fill=(100, 100, 100, 255), font=font_small)
    
    return img
