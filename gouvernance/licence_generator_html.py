"""
Générateur de Licence Sportive utilisant le template HTML essai.html
"""
import io
import os
import tempfile
import qrcode
from django.core.files.base import ContentFile
from django.conf import settings
from xhtml2pdf import pisa


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
    Génère la Licence Sportive Nationale au format ID-1 en utilisant le template HTML.
    Utilise xhtml2pdf pour convertir le HTML en PDF.
    
    Returns:
        ContentFile: Fichier PDF prêt à être sauvegardé
    """
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
        # Charger le template HTML
        base_dir = settings.BASE_DIR
        template_path = os.path.join(base_dir, 'licence_fichier', 'essai.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Remplacer les variables du template
        html_content = _remplacer_variables_template(html_content, athlete, qr_path, base_dir)
        
        # Générer le PDF avec xhtml2pdf
        pdf_buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(
            html_content,
            dest=pdf_buffer,
            path=os.path.join(base_dir, 'licence_fichier')
        )
        
        if pisa_status.err:
            raise Exception(f"Erreur lors de la génération du PDF: {pisa_status.err}")
        
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
        photo_path = athlete.personne.photo.path
    else:
        photo_path = os.path.join(base_dir, 'media', 'sceaux', 'logo-rdc.png')
    
    # Préparer les valeurs
    nom = athlete.personne.nom.upper() if athlete.personne and athlete.personne.nom else ''
    postnom = athlete.personne.postnom.upper() if athlete.personne and athlete.personne.postnom else ''
    prenom = athlete.personne.prenom.upper() if athlete.personne and athlete.personne.prenom else ''
    id_sportif = athlete.numero_licence or athlete.numero_sportif or ''
    discipline = athlete.discipline.designation if athlete.discipline else ''
    
    # Province d'origine
    province = ''
    if athlete.club and athlete.club.institution_tutelle:
        province = athlete.club.institution_tutelle.nom_officiel
    
    # Date de naissance
    date_naissance = ''
    if athlete.personne and athlete.personne.date_naissance:
        date_naissance = athlete.personne.date_naissance.strftime('%d/%m/%Y')
    
    # Groupe sanguin
    groupe_sanguin = athlete.groupe_sanguin if athlete.groupe_sanguin else 'N/A'
    
    # Lieu de naissance
    lieu_naissance = ''
    if athlete.personne and athlete.personne.lieu_naissance:
        lieu_naissance = athlete.personne.lieu_naissance
    
    # Club
    club = athlete.club.nom_officiel if athlete.club else ''
    
    # Adresse (si disponible)
    adresse = ''
    if athlete.personne and hasattr(athlete.personne, 'adresse'):
        adresse = str(athlete.personne.adresse) if athlete.personne.adresse else ''
    
    # Remplacements
    replacements = {
        '{{ athlete.photo.url }}': photo_path,
        '{{ athlete.nom }}': nom,
        '{{ athlete.postnom }}': postnom,
        '{{ athlete.prenom }}': prenom,
        '{{ athlete.id_sportif }}': id_sportif,
        '{{ athlete.discipline.nom }}': discipline,
        '{{ athlete.qr_code.url }}': qr_path,
        '{{ athlete.province.nom }}': province,
        '{{ athlete.date_naissance|date:"d/m/Y" }}': date_naissance,
        '{{ athlete.visite_medicale.groupe_sanguin }}': groupe_sanguin,
        '{{ athlete.lieu_naissance }}': lieu_naissance,
        '{{ athlete.club }}': club,
        '{{ athlete.adresse }}': adresse,
    }
    
    # Appliquer les remplacements
    for key, value in replacements.items():
        html_content = html_content.replace(key, str(value))
    
    return html_content
