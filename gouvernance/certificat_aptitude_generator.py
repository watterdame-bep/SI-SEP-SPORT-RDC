"""
Générateur du Certificat d'Aptitude (F72) — preuve juridique et médicale.
Document officiel généré par le système : identité biométrique, mention d'aptitude,
signature du médecin (nom + n° Ordre), cachet électronique, QR code de vérification.
"""
import io
import textwrap
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
import qrcode
from PIL import Image as PILImage


# Couleurs
BLEU_RDC = HexColor('#0036ca')
NOIR = HexColor('#000000')
GRIS = HexColor('#374151')
GRIS_CLAIR = HexColor('#f3f4f6')


def _generer_qr_image(url):
    """Génère une image QR code en PNG (BytesIO)."""
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=8, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


def generer_certificat_aptitude_pdf(visite, base_url=None):
    """
    Génère le PDF du Certificat d'Aptitude (F72) pour une visite médicale.
    
    Contenu :
    - Identité biométrique : photo de l'athlète + ID National Sportif
    - Mention d'aptitude (phrase standard)
    - Signature numérique : nom du médecin, n° Ordre des Médecins (CNOM), cachet électronique
    - QR code de validation (vérification dans la base)
    
    Args:
        visite: Instance VisiteMedicale (avec athlete, medecin_nom, medecin_numero_ordre, etc.)
        base_url: URL de base du site (pour le lien de vérification)
    
    Returns:
        io.BytesIO: Flux PDF
    """
    from django.conf import settings
    if base_url is None:
        base_url = getattr(settings, 'SITE_URL', getattr(settings, 'SISEP_PUBLIC_URL', 'http://127.0.0.1:8000'))
    base_url = base_url.rstrip('/')
    
    athlete = visite.athlete
    verification_url = f"{base_url}/gouvernance/certificat-aptitude/verifier/{visite.uid}/"
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    
    # ----- En-tête -----
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(BLEU_RDC)
    c.drawCentredString(w/2, h - 1.2*cm, "RÉPUBLIQUE DÉMOCRATIQUE DU CONGO")
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(w/2, h - 1.6*cm, "MINISTÈRE DES SPORTS ET LOISIRS")
    c.setFont("Helvetica", 9)
    c.setFillColor(NOIR)
    c.drawCentredString(w/2, h - 1.95*cm, "SI-SEP Sport — Système d'Information Sport pour l'Excellence et la Performance")
    
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(BLEU_RDC)
    c.drawCentredString(w/2, h - 2.6*cm, "CERTIFICAT D'APTITUDE À LA PRATIQUE DU SPORT EN COMPÉTITION")
    c.setFont("Helvetica", 9)
    c.setFillColor(GRIS)
    c.drawCentredString(w/2, h - 2.9*cm, "Document généré électroniquement — F72")
    
    y = h - 3.5*cm
    
    # ----- Identité biométrique : photo + ID National Sportif -----
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(NOIR)
    c.drawString(1.5*cm, y, "Identité de l'athlète")
    y -= 0.4*cm
    
    photo_x, photo_y = 1.5*cm, y - 4*cm
    photo_w, photo_h = 3*cm, 4*cm
    
    if athlete.personne and getattr(athlete.personne, 'photo', None) and athlete.personne.photo:
        try:
            c.drawImage(athlete.personne.photo.path, photo_x, photo_y, width=photo_w, height=photo_h, preserveAspectRatio=True)
        except Exception:
            c.setStrokeColor(GRIS)
            c.rect(photo_x, photo_y, photo_w, photo_h)
    else:
        c.setStrokeColor(GRIS)
        c.rect(photo_x, photo_y, photo_w, photo_h)
        c.setFont("Helvetica", 8)
        c.setFillColor(GRIS)
        c.drawCentredString(photo_x + photo_w/2, photo_y + photo_h/2 - 0.2*cm, "Photo")
    
    # À droite de la photo : nom, ID sportif
    info_x = photo_x + photo_w + 1*cm
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(GRIS)
    c.drawString(info_x, y - 0.3*cm, "NOM COMPLET")
    c.setFont("Helvetica", 11)
    c.setFillColor(NOIR)
    c.drawString(info_x, y - 0.7*cm, (athlete.nom_complet or "").upper())
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(GRIS)
    c.drawString(info_x, y - 1.2*cm, "ID NATIONAL SPORTIF")
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(BLEU_RDC)
    c.drawString(info_x, y - 1.6*cm, athlete.numero_sportif or "—")
    c.setFont("Helvetica", 9)
    c.setFillColor(NOIR)
    c.drawString(info_x, y - 2.1*cm, f"Club : {(athlete.club.nom_officiel if athlete.club else '—')[:40]}")
    c.drawString(info_x, y - 2.5*cm, f"Discipline : {(athlete.discipline.designation if athlete.discipline else '—')[:35]}")
    
    y = photo_y - 0.8*cm
    
    # ----- Mention d'aptitude (phrase standard) -----
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(NOIR)
    c.drawString(1.5*cm, y, "Certification médicale")
    y -= 0.5*cm
    
    c.setFont("Helvetica", 10)
    phrase_standard = (
        "Le médecin soussigné certifie avoir examiné ce jour l'athlète susnommé "
        "et n'avoir constaté aucune contre-indication à la pratique du sport en compétition."
    )
    if visite.resultat_global == 'APTE_AVEC_RESERVE':
        phrase_standard = (
            "Le médecin soussigné certifie avoir examiné ce jour l'athlète susnommé. "
            "Aptitude à la pratique du sport en compétition avec réserve."
        )
    elif visite.resultat_global == 'INAPTE':
        phrase_standard = (
            "Le médecin soussigné certifie avoir examiné ce jour l'athlète susnommé. "
            "Contre-indication constatée à la pratique du sport en compétition."
        )
    
    for line in textwrap.wrap(phrase_standard, width=85):
        c.drawString(1.5*cm, y, line)
        y -= 0.4*cm
    y -= 0.3*cm
    
    c.setFont("Helvetica", 9)
    c.setFillColor(GRIS)
    c.drawString(1.5*cm, y, f"Date de l'examen : {visite.date_visite.strftime('%d/%m/%Y')}")
    y -= 0.8*cm
    
    # ----- Signature du médecin + N° Ordre + cachet électronique -----
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(NOIR)
    c.drawString(1.5*cm, y, "Médecin inspecteur")
    y -= 0.4*cm
    c.setFont("Helvetica", 11)
    c.drawString(1.5*cm, y, visite.medecin_nom or "—")
    y -= 0.4*cm
    if visite.medecin_numero_ordre:
        c.setFont("Helvetica", 9)
        c.setFillColor(GRIS)
        c.drawString(1.5*cm, y, f"N° Ordre des Médecins (CNOM) : {visite.medecin_numero_ordre}")
        y -= 0.4*cm
    c.setFont("Helvetica", 8)
    c.drawString(1.5*cm, y, "Document généré électroniquement par SI-SEP Sport RDC")
    c.drawString(1.5*cm, y - 0.35*cm, f"Le {datetime.now().strftime('%d/%m/%Y à %H:%M')} — Cachet électronique")
    
    # ----- QR code de validation (en bas à droite) -----
    qr_size = 3*cm
    qr_x = w - 1.5*cm - qr_size
    qr_y = 1.5*cm
    try:
        qr_buf = _generer_qr_image(verification_url)
        # Utiliser ImageReader (BytesIO) ou fichier temporaire pour compatibilité ReportLab
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            qr_buf.seek(0)
            tmp.write(qr_buf.read())
            tmp_path = tmp.name
        try:
            c.drawImage(tmp_path, qr_x, qr_y, width=qr_size, height=qr_size)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Certificat F72: QR code non inséré: %s", e)
    c.setFont("Helvetica", 7)
    c.setFillColor(GRIS)
    c.drawCentredString(qr_x + qr_size/2, qr_y - 0.3*cm, "Scanner pour vérifier")
    c.drawCentredString(qr_x + qr_size/2, qr_y - 0.55*cm, "l'authenticité du certificat")
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
