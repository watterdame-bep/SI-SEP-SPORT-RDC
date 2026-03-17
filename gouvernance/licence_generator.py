"""
Générateur de Licence Sportive pour les Athlètes Certifiés Nationalement.
Utilise le template HTML essai.html du dossier licence_fichier/
pour créer une carte d'identité sportive avec les données de l'athlète.
"""
import io
import os
import tempfile
import qrcode
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile
from django.conf import settings
from django.template.loader import render_to_string

# Format ID-1 (ISO/IEC 7810) — carte bancaire, permis de conduire, licence sportive RDC
ID1_LARGEUR_MM = 85.60
ID1_HAUTEUR_MM = 53.98
ID1_PAGESIZE = (ID1_LARGEUR_MM * mm, ID1_HAUTEUR_MM * mm)
ID1_RAYON_COINS_MM = 3.18

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


def generer_licence_sportive(athlete, base_url=None):
    """
    Génère la Licence Sportive Nationale en PDF.
    Document officiel généré automatiquement lors de la certification nationale.
    
    Args:
        athlete: Instance du modèle Athlete
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
    # Bordure externe (Bleu Royal 3pt)
    c.setLineWidth(3)
    c.setStrokeColor(BLEU_ROYAL)
    c.rect(0.5*cm, 0.5*cm, largeur - 1*cm, hauteur - 1*cm)
    
    # Liseré intérieur (Jaune 2pt)
    c.setLineWidth(2)
    c.setStrokeColor(JAUNE_DRAPEAU)
    c.rect(0.8*cm, 0.8*cm, largeur - 1.6*cm, hauteur - 1.6*cm)
    
    # ===== EN-TÊTE OFFICIEL =====
    y_pos = hauteur - 1.5*cm
    
    # Logo RDC au centre
    try:
        logo_path = 'media/sceaux/logo-rdc.png'
        logo_x = largeur/2 - 1*cm
        logo_y = hauteur - 2.5*cm
        
        c.drawImage(
            logo_path,
            logo_x,
            logo_y,
            width=2*cm,
            height=2*cm,
            preserveAspectRatio=True
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Impossible d'insérer le logo RDC: {str(e)}")
    
    y_pos -= 2.5*cm
    
    # Texte en-tête
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(NOIR)
    c.drawCentredString(largeur/2, y_pos, "RÉPUBLIQUE DÉMOCRATIQUE DU CONGO")
    
    y_pos -= 0.5*cm
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(BLEU_ROYAL)
    c.drawCentredString(largeur/2, y_pos, "MINISTÈRE DES SPORTS ET LOISIRS")
    
    y_pos -= 0.4*cm
    c.setFont("Helvetica", 9)
    c.setFillColor(NOIR)
    federation = athlete.club.institution_tutelle if athlete.club else None
    if federation:
        c.drawCentredString(largeur/2, y_pos, federation.nom_officiel.upper())
    
    y_pos -= 0.8*cm
    
    # ===== TITRE PRINCIPAL =====
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(BLEU_ROYAL)
    c.drawCentredString(largeur/2, y_pos, "LICENCE SPORTIVE NATIONALE")
    
    y_pos -= 0.5*cm
    
    # Saison sportive
    c.setFont("Helvetica", 10)
    c.setFillColor(NOIR)
    annee = datetime.now().year
    c.drawCentredString(largeur/2, y_pos, f"Saison {annee}-{annee+1}")
    
    y_pos -= 1*cm
    
    # ===== PHOTO ET INFORMATIONS PRINCIPALES =====
    # Photo de l'athlète (gauche)
    photo_x = 2*cm
    photo_y = y_pos - 4*cm
    photo_width = 3*cm
    photo_height = 4*cm
    
    if athlete.personne and athlete.personne.photo:
        try:
            c.drawImage(
                athlete.personne.photo.path,
                photo_x,
                photo_y,
                width=photo_width,
                height=photo_height,
                preserveAspectRatio=True
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Impossible d'insérer la photo de l'athlète: {str(e)}")
            # Dessiner un cadre vide
            c.setStrokeColor(GRIS_CLAIR)
            c.rect(photo_x, photo_y, photo_width, photo_height)
    else:
        # Dessiner un cadre vide
        c.setStrokeColor(GRIS_CLAIR)
        c.rect(photo_x, photo_y, photo_width, photo_height)
    
    # Informations à droite de la photo
    info_x = photo_x + photo_width + 1*cm
    info_y = y_pos - 0.5*cm
    
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(BLEU_ROYAL)
    c.drawString(info_x, info_y, "NUMÉRO DE LICENCE")
    
    info_y -= 0.5*cm
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(ROUGE_DRAPEAU)
    c.drawString(info_x, info_y, athlete.numero_licence or athlete.numero_sportif)
    
    info_y -= 0.8*cm
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(NOIR)
    c.drawString(info_x, info_y, "NOM COMPLET")
    
    info_y -= 0.4*cm
    c.setFont("Helvetica", 10)
    c.drawString(info_x, info_y, athlete.nom_complet.upper())
    
    info_y -= 0.6*cm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(info_x, info_y, "DATE DE NAISSANCE")
    
    info_y -= 0.4*cm
    c.setFont("Helvetica", 10)
    if athlete.personne and athlete.personne.date_naissance:
        c.drawString(info_x, info_y, athlete.personne.date_naissance.strftime('%d/%m/%Y'))
    
    info_y -= 0.6*cm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(info_x, info_y, "SEXE")
    
    info_y -= 0.4*cm
    c.setFont("Helvetica", 10)
    if athlete.personne:
        sexe_text = "Masculin" if athlete.personne.sexe == 'M' else "Féminin"
        c.drawString(info_x, info_y, sexe_text)
    
    y_pos = photo_y - 1*cm
    
    # ===== INFORMATIONS SPORTIVES =====
    # Cadre avec fond bleu clair
    cadre_y = y_pos - 3.5*cm
    c.setFillColor(HexColor('#e6f0ff'))
    c.rect(1.5*cm, cadre_y, largeur - 3*cm, 3*cm, fill=1, stroke=0)
    
    # Bordure du cadre
    c.setStrokeColor(BLEU_ROYAL)
    c.setLineWidth(1)
    c.rect(1.5*cm, cadre_y, largeur - 3*cm, 3*cm)
    
    # Contenu du cadre
    cadre_x = 2*cm
    cadre_y_text = cadre_y + 2.5*cm
    
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(BLEU_ROYAL)
    c.drawString(cadre_x, cadre_y_text, "DISCIPLINE")
    
    cadre_y_text -= 0.4*cm
    c.setFont("Helvetica", 10)
    c.setFillColor(NOIR)
    if athlete.discipline:
        c.drawString(cadre_x, cadre_y_text, athlete.discipline.designation)
    
    cadre_y_text -= 0.7*cm
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(BLEU_ROYAL)
    c.drawString(cadre_x, cadre_y_text, "CLUB")
    
    cadre_y_text -= 0.4*cm
    c.setFont("Helvetica", 10)
    c.setFillColor(NOIR)
    if athlete.club:
        c.drawString(cadre_x, cadre_y_text, athlete.club.nom_officiel)
    
    cadre_y_text -= 0.7*cm
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(BLEU_ROYAL)
    c.drawString(cadre_x, cadre_y_text, "PROVINCE")
    
    cadre_y_text -= 0.4*cm
    c.setFont("Helvetica", 10)
    c.setFillColor(NOIR)
    if athlete.club and athlete.club.institution_tutelle:
        province_text = athlete.club.institution_tutelle.nom_officiel
        c.drawString(cadre_x, cadre_y_text, province_text)
    
    # Colonne droite du cadre
    cadre_x2 = largeur/2 + 1*cm
    cadre_y_text = cadre_y + 2.5*cm
    
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(BLEU_ROYAL)
    c.drawString(cadre_x2, cadre_y_text, "CATÉGORIE")
    
    cadre_y_text -= 0.4*cm
    c.setFont("Helvetica", 10)
    c.setFillColor(NOIR)
    c.drawString(cadre_x2, cadre_y_text, athlete.get_categorie_display())
    
    cadre_y_text -= 0.7*cm
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(BLEU_ROYAL)
    c.drawString(cadre_x2, cadre_y_text, "POSTE")
    
    cadre_y_text -= 0.4*cm
    c.setFont("Helvetica", 10)
    c.setFillColor(NOIR)
    c.drawString(cadre_x2, cadre_y_text, athlete.poste or "—")
    
    cadre_y_text -= 0.7*cm
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(BLEU_ROYAL)
    c.drawString(cadre_x2, cadre_y_text, "N° MAILLOT")
    
    cadre_y_text -= 0.4*cm
    c.setFont("Helvetica", 10)
    c.setFillColor(NOIR)
    c.drawString(cadre_x2, cadre_y_text, str(athlete.numero_maillot) if athlete.numero_maillot else "—")
    
    y_pos = cadre_y - 1*cm
    
    # ===== VALIDITÉ =====
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(BLEU_ROYAL)
    c.drawString(1.5*cm, y_pos, "VALIDITÉ DE LA LICENCE")
    
    y_pos -= 0.5*cm
    c.setFont("Helvetica", 10)
    c.setFillColor(NOIR)
    
    if athlete.date_emission_licence and athlete.date_expiration_licence:
        texte_validite = f"Du {athlete.date_emission_licence.strftime('%d/%m/%Y')} au {athlete.date_expiration_licence.strftime('%d/%m/%Y')}"
        c.drawString(1.5*cm, y_pos, texte_validite)
    
    y_pos -= 0.8*cm
    
    # ===== QR CODE (bas gauche) =====
    qr_url = f"{base_url}/gouvernance/verifier-athlete/{athlete.uid}/"
    qr_img = generer_qr_code(qr_url)
    
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        qr_img.save(tmp_file.name, format='PNG')
        qr_path = tmp_file.name
    
    qr_x = 1.5*cm
    qr_y = 2*cm
    try:
        c.drawImage(qr_path, qr_x, qr_y, width=2*cm, height=2*cm)
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
    c.drawString(qr_x, qr_y - 0.3*cm, "Vérifier en ligne")
    
    # ===== SIGNATURE ET CACHET (bas droit) =====
    sig_x = largeur - 6*cm
    sig_y = 3.5*cm
    
    c.setFont("Helvetica", 8)
    c.setFillColor(NOIR)
    
    # Date et lieu
    date_jour = datetime.now().strftime("%d/%m/%Y")
    c.drawString(sig_x, sig_y, f"Fait à Kinshasa, le {date_jour}")
    
    sig_y -= 0.5*cm
    
    # Titre
    c.setFont("Helvetica-Bold", 8)
    c.drawString(sig_x, sig_y, "Pour la Fédération,")
    
    sig_y -= 0.3*cm
    c.setFont("Helvetica", 7)
    c.drawString(sig_x, sig_y, "Le Secrétaire Général")
    
    sig_y -= 1*cm
    
    # Espace pour signature
    c.setLineWidth(1)
    c.setStrokeColor(NOIR)
    c.line(sig_x, sig_y, sig_x + 3*cm, sig_y)
    
    sig_y -= 0.3*cm
    c.setFont("Helvetica", 7)
    c.drawString(sig_x + 0.5*cm, sig_y, "Signature & Cachet")
    
    # ===== PIED DE PAGE =====
    c.setFont("Helvetica", 7)
    c.setFillColor(GRIS_CLAIR)
    c.drawString(1.5*cm, 1*cm, f"Licence générée le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
    c.drawRightString(largeur - 1.5*cm, 1*cm, f"N° {athlete.numero_licence or athlete.numero_sportif}")
    
    # Avertissement au verso (optionnel)
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(ROUGE_DRAPEAU)
    c.drawCentredString(largeur/2, 0.7*cm, "Document officiel - Toute falsification est passible de sanctions")
    
    # Finaliser le PDF
    c.save()
    
    # Retourner le contenu
    buffer.seek(0)
    numero_fichier = athlete.numero_licence or athlete.numero_sportif
    return ContentFile(buffer.getvalue(), name=f"Licence_{numero_fichier}.pdf")


def generer_licence_sportive_id1_html(athlete, base_url=None):
    """
    Génère la Licence Sportive Nationale au format ID-1 en utilisant le template HTML.
    Utilise weasyprint pour convertir le HTML en PDF de haute qualité.
    
    Returns:
        ContentFile: Fichier PDF prêt à être sauvegardé
    """
    try:
        from weasyprint import HTML, CSS
    except ImportError:
        # Fallback sur l'ancienne méthode si weasyprint n'est pas installé
        return generer_licence_sportive_id1_image(athlete, base_url)
    
    if base_url is None:
        base_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
    base_url = base_url.rstrip('/')
    
    # Générer le QR code
    qr_url = f"{base_url}/gouvernance/verifier-athlete/{athlete.uid}/"
    qr_img = generer_qr_code(qr_url)
    
    # Sauvegarder le QR code temporairement
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_qr:
        qr_img.save(tmp_qr.name, format='PNG')
        qr_path = tmp_qr.name
    
    try:
        # Préparer le contexte pour le template
        context = {
            'athlete': athlete,
            'qr_code_path': qr_path,
            'base_dir': settings.BASE_DIR,
        }
        
        # Charger et rendre le template HTML
        base_dir = settings.BASE_DIR
        template_path = os.path.join(base_dir, 'licence_fichier', 'essai.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Remplacer les variables du template
        html_content = _remplacer_variables_template(html_content, athlete, qr_path, base_dir)
        
        # Générer le PDF avec weasyprint
        pdf_buffer = io.BytesIO()
        HTML(string=html_content, base_url=str(base_dir)).write_pdf(pdf_buffer)
        pdf_buffer.seek(0)
        
        numero_fichier = athlete.numero_licence or athlete.numero_sportif or str(athlete.uid)[:8]
        return ContentFile(pdf_buffer.getvalue(), name=f"Licence_ID1_{numero_fichier}.pdf")
        
    finally:
        # Nettoyer le fichier QR temporaire
        try:
            os.unlink(qr_path)
        except:
            pass


def _remplacer_variables_template(html_content, athlete, qr_path, base_dir):
    """
    Remplace les variables Django template par les vraies valeurs
    """
    # Photo de l'athlète
    if athlete.personne and athlete.personne.photo:
        photo_url = athlete.personne.photo.path
    else:
        photo_url = os.path.join(base_dir, 'media', 'sceaux', 'logo-rdc.png')
    
    # Remplacements
    replacements = {
        '{{ athlete.photo.url }}': photo_url,
        '{{ athlete.nom }}': athlete.personne.nom.upper() if athlete.personne and athlete.personne.nom else '',
        '{{ athlete.postnom }}': athlete.personne.postnom.upper() if athlete.personne and athlete.personne.postnom else '',
        '{{ athlete.prenom }}': athlete.personne.prenom.upper() if athlete.personne and a
    """
    Génère la Licence Sportive Nationale au format ID-1 (85,60 mm × 53,98 mm).
    Utilise les templates recto.png et verso.png du dossier licence_fichier/
    et superpose les informations de l'athlète (photo, numéro, discipline).
    
    Returns:
        ContentFile: Fichier PDF recto-verso prêt à être sauvegardé
    """
    if base_url is None:
        base_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
    base_url = base_url.rstrip('/')

    # Chemins des templates
    base_dir = getattr(settings, 'BASE_DIR', os.path.dirname(os.path.dirname(__file__)))
    recto_template_path = os.path.join(base_dir, 'licence_fichier', 'recto.png')
    verso_template_path = os.path.join(base_dir, 'licence_fichier', 'verso.png')

    # Créer les images recto et verso avec superposition
    recto_image = _creer_recto_licence(athlete, recto_template_path, base_url)
    verso_image = _creer_verso_licence(athlete, verso_template_path, base_url)

    # Créer le PDF avec les deux pages
    buffer = io.BytesIO()
    w, h = ID1_PAGESIZE
    c = canvas.Canvas(buffer, pagesize=ID1_PAGESIZE)

    # Page 1: Recto
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_recto:
        recto_image.save(tmp_recto.name, format='PNG', dpi=(300, 300))
        tmp_recto_path = tmp_recto.name
    
    try:
        c.drawImage(tmp_recto_path, 0, 0, width=w, height=h)
        c.showPage()
    finally:
        try:
            os.unlink(tmp_recto_path)
        except:
            pass

    # Page 2: Verso
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_verso:
        verso_image.save(tmp_verso.name, format='PNG', dpi=(300, 300))
        tmp_verso_path = tmp_verso.name
    
    try:
        c.drawImage(tmp_verso_path, 0, 0, width=w, height=h)
    finally:
        try:
            os.unlink(tmp_verso_path)
        except:
            pass

    c.save()
    buffer.seek(0)
    
    numero_fichier = athlete.numero_licence or athlete.numero_sportif or str(athlete.uid)[:8]
    return ContentFile(buffer.getvalue(), name=f"Licence_ID1_{numero_fichier}.pdf")


def _creer_recto_licence(athlete, template_path, base_url):
    """
    Crée l'image recto de la licence en superposant les données sur le template.
    Layout: Photo à gauche, informations complètes à droite, QR code en bas à gauche
    """
    # Charger le template
    if os.path.exists(template_path):
        img = Image.open(template_path).convert('RGBA')
    else:
        # Créer une image vide si template absent
        img = Image.new('RGBA', (1011, 638), (255, 255, 255, 255))
    
    draw = ImageDraw.Draw(img)
    
    # Charger des polices avec différentes tailles
    try:
        font_numero = ImageFont.truetype("arialbd.ttf", 32)  # Numéro athlète
        font_label = ImageFont.truetype("arialbd.ttf", 16)   # Labels (NOM, PRENOM, etc.)
        font_value = ImageFont.truetype("arial.ttf", 18)     # Valeurs
        font_small = ImageFont.truetype("arial.ttf", 14)     # Petits textes
    except:
        font_numero = ImageFont.load_default()
        font_label = ImageFont.load_default()
        font_value = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # === PHOTO DE L'ATHLÈTE (gauche, centrée verticalement) ===
    photo_x = 40
    photo_y = 120
    photo_width = 180
    photo_height = 240
    
    if athlete.personne and athlete.personne.photo:
        try:
            photo = Image.open(athlete.personne.photo.path).convert('RGBA')
            photo = photo.resize((photo_width, photo_height), Image.Resampling.LANCZOS)
            img.paste(photo, (photo_x, photo_y), photo)
        except Exception as e:
            print(f"Erreur chargement photo: {e}")
            # Dessiner un cadre vide
            draw.rectangle([(photo_x, photo_y), (photo_x + photo_width, photo_y + photo_height)], 
                          outline=(200, 200, 200, 255), width=2)
    else:
        # Dessiner un cadre vide
        draw.rectangle([(photo_x, photo_y), (photo_x + photo_width, photo_y + photo_height)], 
                      outline=(200, 200, 200, 255), width=2)
    
    # === INFORMATIONS À DROITE DE LA PHOTO ===
    info_x = photo_x + photo_width + 30  # Marge de 30px après la photo
    info_y_start = 100
    line_height = 35
    
    # Numéro athlète (en rouge, grand)
    numero = athlete.numero_licence or athlete.numero_sportif or "—"
    draw.text((info_x, info_y_start), f"N° {numero}", 
             fill=(237, 28, 36, 255), font=font_numero)
    
    current_y = info_y_start + 50
    
    # NOM
    if athlete.personne and athlete.personne.nom:
        draw.text((info_x, current_y), "NOM:", fill=(100, 100, 100, 255), font=font_label)
        draw.text((info_x + 120, current_y), athlete.personne.nom.upper(), 
                 fill=(0, 0, 0, 255), font=font_value)
        current_y += line_height
    
    # POST-NOM
    if athlete.personne and athlete.personne.postnom:
        draw.text((info_x, current_y), "POST-NOM:", fill=(100, 100, 100, 255), font=font_label)
        draw.text((info_x + 120, current_y), athlete.personne.postnom.upper(), 
                 fill=(0, 0, 0, 255), font=font_value)
        current_y += line_height
    
    # PRÉNOM
    if athlete.personne and athlete.personne.prenom:
        draw.text((info_x, current_y), "PRÉNOM:", fill=(100, 100, 100, 255), font=font_label)
        draw.text((info_x + 120, current_y), athlete.personne.prenom.upper(), 
                 fill=(0, 0, 0, 255), font=font_value)
        current_y += line_height
    
    # DATE DE NAISSANCE
    if athlete.personne and athlete.personne.date_naissance:
        draw.text((info_x, current_y), "NÉ(E) LE:", fill=(100, 100, 100, 255), font=font_label)
        draw.text((info_x + 120, current_y), 
                 athlete.personne.date_naissance.strftime('%d/%m/%Y'), 
                 fill=(0, 0, 0, 255), font=font_value)
        current_y += line_height
    
    # LIEU DE NAISSANCE
    if athlete.personne and athlete.personne.lieu_naissance:
        draw.text((info_x, current_y), "À:", fill=(100, 100, 100, 255), font=font_label)
        lieu = athlete.personne.lieu_naissance[:30]  # Limiter la longueur
        draw.text((info_x + 120, current_y), lieu, 
                 fill=(0, 0, 0, 255), font=font_value)
        current_y += line_height
    
    # DISCIPLINE (en bleu)
    if athlete.discipline:
        draw.text((info_x, current_y), "DISCIPLINE:", fill=(100, 100, 100, 255), font=font_label)
        draw.text((info_x + 120, current_y), athlete.discipline.designation[:25], 
                 fill=(0, 54, 202, 255), font=font_value)
        current_y += line_height
    
    # CLUB
    if athlete.club:
        draw.text((info_x, current_y), "CLUB:", fill=(100, 100, 100, 255), font=font_label)
        club_text = athlete.club.nom_officiel[:30]
        draw.text((info_x + 120, current_y), club_text, 
                 fill=(0, 0, 0, 255), font=font_value)
        current_y += line_height
    
    # ADRESSE (si disponible dans le modèle Personne)
    if athlete.personne and hasattr(athlete.personne, 'adresse') and athlete.personne.adresse:
        draw.text((info_x, current_y), "ADRESSE:", fill=(100, 100, 100, 255), font=font_label)
        adresse = str(athlete.personne.adresse)[:35]
        draw.text((info_x + 120, current_y), adresse, 
                 fill=(0, 0, 0, 255), font=font_small)
    
    # === QR CODE EN BAS À GAUCHE ===
    qr_url = f"{base_url}/gouvernance/verifier-athlete/{athlete.uid}/"
    qr_img = generer_qr_code(qr_url)
    qr_size = 100
    qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
    
    # Position en bas à gauche avec marge
    qr_x = 40
    qr_y = 638 - qr_size - 30
    img.paste(qr_img, (qr_x, qr_y))
    
    # Texte sous le QR code
    draw.text((qr_x + qr_size//2 - 30, qr_y + qr_size + 5), 
             "Vérifier", fill=(100, 100, 100, 255), font=font_small)
    
    return img


def _creer_verso_licence(athlete, template_path, base_url):
    """
    Crée l'image verso de la licence en superposant les données sur le template.
    Superpose: dates de validité, informations complémentaires
    """
    # Charger le template
    if os.path.exists(template_path):
        img = Image.open(template_path).convert('RGBA')
    else:
        # Créer une image vide si template absent
        img = Image.new('RGBA', (1011, 638), (255, 255, 255, 255))
    
    draw = ImageDraw.Draw(img)
    
    # Charger des polices
    try:
        font_title = ImageFont.truetype("arialbd.ttf", 20)
        font_regular = ImageFont.truetype("arial.ttf", 18)
        font_small = ImageFont.truetype("arial.ttf", 14)
    except:
        font_title = ImageFont.load_default()
        font_regular = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Position de départ
    x_start = 100
    y_start = 150
    line_height = 40
    
    # VALIDITÉ DE LA LICENCE
    draw.text((x_start, y_start), "VALIDITÉ DE LA LICENCE", 
             fill=(0, 54, 202, 255), font=font_title)
    
    current_y = y_start + 40
    
    if athlete.date_emission_licence and athlete.date_expiration_licence:
        validite_text = f"Valide du {athlete.date_emission_licence.strftime('%d/%m/%Y')}"
        draw.text((x_start, current_y), validite_text, 
                 fill=(0, 0, 0, 255), font=font_regular)
        current_y += 30
        
        validite_text2 = f"au {athlete.date_expiration_licence.strftime('%d/%m/%Y')}"
        draw.text((x_start, current_y), validite_text2, 
                 fill=(0, 0, 0, 255), font=font_regular)
        current_y += line_height + 20
    
    # INFORMATIONS COMPLÉMENTAIRES
    if athlete.poste:
        draw.text((x_start, current_y), f"Poste: {athlete.poste}", 
                 fill=(0, 0, 0, 255), font=font_regular)
        current_y += line_height
    
    if athlete.numero_maillot:
        draw.text((x_start, current_y), f"N° Maillot: {athlete.numero_maillot}", 
                 fill=(0, 0, 0, 255), font=font_regular)
        current_y += line_height
    
    # Catégorie
    draw.text((x_start, current_y), f"Catégorie: {athlete.get_categorie_display()}", 
             fill=(0, 0, 0, 255), font=font_regular)
    
    # Texte de sécurité en bas
    security_text = "Document officiel - Toute falsification est passible de sanctions"
    draw.text((x_start, 638 - 50), security_text, 
             fill=(237, 28, 36, 255), font=font_small)
    
    return img


def _draw_photo_placeholder(canvas, x, y, w, h):
    """Dessine un cadre vide pour la photo si absente."""
    canvas.setStrokeColor(GRIS_CLAIR)
    canvas.setFillColor(HexColor('#f3f4f6'))
    canvas.rect(x, y, w, h, fill=1, stroke=1)
    canvas.setFillColor(HexColor('#9ca3af'))
    canvas.setFont("Helvetica", 6)
    canvas.drawCentredString(x + w / 2, y + h / 2 - 1.5 * mm, "Photo")
