"""
Générateur de Licence Sportive pour les Athlètes Certifiés Nationalement.
- generer_licence_sportive: Format A4 (legacy).
- generer_licence_sportive_id1: Format ID-1 (85,60 mm × 53,98 mm), norme carte bancaire / permis,
  licence biométrique sécurisée (QR code, photo, logo fédération, numéro national sportif).
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
from PIL import Image
from django.core.files.base import ContentFile

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


def generer_licence_sportive_id1(athlete, base_url=None):
    """
    Génère la Licence Sportive Nationale au format ID-1 (85,60 mm × 53,98 mm).
    Norme RDC / FECOFA : carte biométrique sécurisée (photo, QR code, logo, numéro national).
    Recto uniquement dans ce PDF ; impression recto-verso possible via le template HTML F22.
    
    Returns:
        io.BytesIO: flux PDF (à sauvegarder dans athlete.licence_pdf).
    """
    from django.conf import settings
    if base_url is None:
        base_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
    base_url = base_url.rstrip('/')

    buffer = io.BytesIO()
    w, h = ID1_PAGESIZE
    c = canvas.Canvas(buffer, pagesize=ID1_PAGESIZE)

    # Coins arrondis simulés par un rectangle (la découpe physique se fait à l'impression)
    r = ID1_RAYON_COINS_MM * mm
    c.setLineWidth(0.5)
    c.setStrokeColor(BLEU_ROYAL)
    c.setFillColor(HexColor('#ffffff'))
    c.roundRect(0, 0, w, h, r, fill=1, stroke=1)

    # Filigrane / fond discret (drapeau RDC - bandes très atténuées)
    c.setFillColor(HexColor('#0036ca'))
    c.setFillAlpha(0.06)
    c.setStrokeAlpha(0.06)
    c.rect(0, 0, w, h / 3)
    c.setFillColor(HexColor('#FDE015'))
    c.rect(0, h / 3, w, h / 3)
    c.setFillColor(HexColor('#ED1C24'))
    c.rect(0, 2 * h / 3, w, h / 3)
    c.setFillAlpha(1)
    c.setStrokeAlpha(1)

    # --- Photo biométrique (gauche) ---
    photo_x, photo_y = 2 * mm, h - 10 * mm
    photo_w, photo_h = 18 * mm, 22 * mm
    if athlete.personne and getattr(athlete.personne, 'photo', None) and athlete.personne.photo:
        try:
            c.drawImage(athlete.personne.photo.path, photo_x, photo_y, width=photo_w, height=photo_h, preserveAspectRatio=True)
        except Exception:
            _draw_photo_placeholder(c, photo_x, photo_y, photo_w, photo_h)
    else:
        _draw_photo_placeholder(c, photo_x, photo_y, photo_w, photo_h)
    c.setStrokeColor(BLEU_ROYAL)
    c.setLineWidth(0.3)
    c.rect(photo_x, photo_y, photo_w, photo_h)

    # --- Logo fédération / RDC (droite, haut) ---
    logo_x = w - 20 * mm
    logo_y = h - 14 * mm
    logo_w = 16 * mm
    logo_h = 10 * mm
    federation = athlete.club.institution_tutelle if athlete.club else None
    logo_path = None
    if federation and getattr(federation, 'logo', None) and federation.logo:
        try:
            logo_path = federation.logo.path
        except Exception:
            pass
    if not logo_path and getattr(settings, 'STATIC_ROOT', None):
        logo_path = os.path.join(settings.STATIC_ROOT, 'img', 'logo-rdc.png')
    if not logo_path and getattr(settings, 'BASE_DIR', None):
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo-rdc.png')
    if logo_path and os.path.isfile(logo_path):
        try:
            c.drawImage(logo_path, logo_x, logo_y, width=logo_w, height=logo_h, preserveAspectRatio=True)
        except Exception:
            pass
    c.setFont("Helvetica-Bold", 6)
    c.setFillColor(BLEU_ROYAL)
    if federation:
        nom_fed = (getattr(federation, 'nom_officiel', None) or getattr(federation, 'designation', None) or "Fédération")[:25]
        c.drawString(logo_x, logo_y - 2 * mm, nom_fed.upper())

    # --- Titre et numéro national sportif ---
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(BLEU_ROYAL)
    c.drawString(photo_x + photo_w + 2 * mm, h - 5 * mm, "RÉPUBLIQUE DÉMOCRATIQUE DU CONGO")
    c.setFont("Helvetica", 6)
    c.setFillColor(NOIR)
    c.drawString(photo_x + photo_w + 2 * mm, h - 7 * mm, "LICENCE SPORTIVE NATIONALE — F22")
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(ROUGE_DRAPEAU)
    c.drawString(photo_x + photo_w + 2 * mm, h - 10 * mm, athlete.numero_licence or athlete.numero_sportif or "—")
    c.setFont("Helvetica-Bold", 6)
    c.setFillColor(NOIR)
    c.drawString(photo_x + photo_w + 2 * mm, h - 11.5 * mm, "N° NATIONAL SPORTIF")

    # --- Nom, date naissance, discipline ---
    info_x = photo_x + photo_w + 2 * mm
    info_y = h - 14 * mm
    c.setFont("Helvetica-Bold", 6)
    c.setFillColor(GRIS_CLAIR)
    c.drawString(info_x, info_y, "NOM COMPLET")
    c.setFont("Helvetica", 7)
    c.setFillColor(NOIR)
    nom_complet = (athlete.nom_complet or "").upper()[:28]
    c.drawString(info_x, info_y - 2.2 * mm, nom_complet)
    c.setFont("Helvetica-Bold", 6)
    c.setFillColor(GRIS_CLAIR)
    c.drawString(info_x, info_y - 4.5 * mm, "NÉ(E) LE")
    c.setFont("Helvetica", 7)
    c.setFillColor(NOIR)
    if athlete.personne and athlete.personne.date_naissance:
        c.drawString(info_x, info_y - 6 * mm, athlete.personne.date_naissance.strftime('%d/%m/%Y'))
    c.setFont("Helvetica-Bold", 6)
    c.setFillColor(GRIS_CLAIR)
    c.drawString(info_x, info_y - 8 * mm, "DISCIPLINE")
    c.setFont("Helvetica", 7)
    c.setFillColor(NOIR)
    if athlete.discipline:
        c.drawString(info_x, info_y - 9.5 * mm, (athlete.discipline.designation or "")[:20])
    if athlete.club:
        c.setFont("Helvetica", 5)
        c.setFillColor(HexColor('#374151'))
        c.drawString(info_x, info_y - 11 * mm, (athlete.club.nom_officiel or "")[:24])

    # --- Validité ---
    c.setFont("Helvetica", 5)
    c.setFillColor(NOIR)
    if athlete.date_emission_licence and athlete.date_expiration_licence:
        c.drawString(photo_x, 8 * mm, f"Valide du {athlete.date_emission_licence.strftime('%d/%m/%Y')} au {athlete.date_expiration_licence.strftime('%d/%m/%Y')}")

    # --- QR code (verso simulé = bas de carte) ---
    qr_url = f"{base_url}/gouvernance/verifier-athlete/{athlete.uid}/"
    qr_img = generer_qr_code(qr_url)
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        qr_img.save(tmp.name, format='PNG')
        qr_path = tmp.name
    try:
        qr_size = 12 * mm
        qr_x = w - qr_size - 3 * mm
        qr_y = 2 * mm
        c.drawImage(qr_path, qr_x, qr_y, width=qr_size, height=qr_size)
    except Exception:
        pass
    finally:
        try:
            os.unlink(qr_path)
        except Exception:
            pass
    c.setFont("Helvetica", 4)
    c.setFillColor(HexColor('#6b7280'))
    c.drawCentredString(qr_x + qr_size / 2, qr_y - 1.5 * mm, "Scanner vérification")

    c.save()
    buffer.seek(0)
    return buffer


def _draw_photo_placeholder(canvas, x, y, w, h):
    """Dessine un cadre vide pour la photo si absente."""
    canvas.setStrokeColor(GRIS_CLAIR)
    canvas.setFillColor(HexColor('#f3f4f6'))
    canvas.rect(x, y, w, h, fill=1, stroke=1)
    canvas.setFillColor(HexColor('#9ca3af'))
    canvas.setFont("Helvetica", 6)
    canvas.drawCentredString(x + w / 2, y + h / 2 - 1.5 * mm, "Photo")
