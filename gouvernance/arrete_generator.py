"""
Générateur d'Arrêté Ministériel d'Agrément pour les Fédérations Sportives.
Produit un document PDF officiel avec signature et sceau du Ministre.
"""
from datetime import datetime
from io import BytesIO
import os
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfgen import canvas
import qrcode
from PIL import Image as PILImage


def generer_numero_arrete(annee=None):
    """
    Génère un numéro d'arrêté unique au format: N°XXX/MIN/SPORTS/YYYY
    XXX = numéro séquentiel de l'année
    """
    from gouvernance.models import Institution
    
    if annee is None:
        annee = datetime.now().year
    
    # Compter les arrêtés déjà signés cette année
    count = Institution.objects.filter(
        numero_arrete__contains=f'/MIN/SL/{annee}',
        statut_signature='SIGNE'
    ).count()
    
    numero_seq = count + 1
    return f"N°{numero_seq:03d}/MIN/SL/{annee}"


def redimensionner_image(image_path, max_width_cm, max_height_cm):
    """
    Redimensionne une image pour qu'elle ne dépasse pas les dimensions max.
    Préserve le ratio d'aspect.
    Retourne un BytesIO avec l'image redimensionnée en PNG.
    """
    try:
        # Ouvrir l'image
        img = PILImage.open(image_path)
        
        # Convertir en RGBA si nécessaire (pour préserver la transparence)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Convertir cm en pixels (1 cm ≈ 37.8 pixels à 96 DPI)
        max_width_px = int(max_width_cm * 37.8)
        max_height_px = int(max_height_cm * 37.8)
        
        # Calculer le ratio d'aspect
        ratio = min(max_width_px / img.width, max_height_px / img.height)
        
        # Redimensionner si nécessaire
        if ratio < 1:
            new_width = int(img.width * ratio)
            new_height = int(img.height * ratio)
            img = img.resize((new_width, new_height), PILImage.Resampling.LANCZOS)
        
        # Sauvegarder en PNG dans un BytesIO
        output = BytesIO()
        img.save(output, format='PNG')
        output.seek(0)
        
        return output
    except Exception as e:
        print(f"Erreur lors du redimensionnement de l'image: {e}")
        return None


def generer_arrete_agrement(institution):
    """
    Génère le PDF de l'Arrêté Ministériel d'Agrément pour une fédération.
    Récupère la signature et le sceau depuis le profil du Ministre.
    """
    from gouvernance.models import Membre
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=3*cm,
        bottomMargin=3*cm,
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    style_header = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading1'],
        fontSize=11,
        textColor=colors.HexColor('#0036ca'),
        alignment=TA_CENTER,
        spaceAfter=6,
        fontName='Helvetica-Bold',
    )
    
    style_title = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.black,
        alignment=TA_CENTER,
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold',
    )
    
    style_body = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=10,
        leading=16,
    )
    
    style_article = ParagraphStyle(
        'CustomArticle',
        parent=styles['BodyText'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
        leftIndent=1*cm,
        fontName='Helvetica-Bold',
    )
    
    style_signature = ParagraphStyle(
        'CustomSignature',
        parent=styles['BodyText'],
        fontSize=11,
        alignment=TA_RIGHT,
        spaceAfter=6,
        fontName='Helvetica-Bold',
    )
    
    story = []
    
    # Logo RDC
    logo_path = os.path.join(settings.BASE_DIR, 'public', 'assets', 'images', 'logo-rdc.png')
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=2*cm, height=2*cm)
            logo.hAlign = 'CENTER'
            story.append(logo)
            story.append(Spacer(1, 0.3*cm))
        except:
            pass
    
    # En-tête officiel
    story.append(Paragraph("RÉPUBLIQUE DÉMOCRATIQUE DU CONGO", style_header))
    story.append(Paragraph("MINISTÈRE DES SPORTS ET LOISIRS", style_header))
    story.append(Spacer(1, 0.5*cm))
    
    # Numéro d'arrêté et date
    numero_arrete = institution.numero_arrete or generer_numero_arrete()
    date_signature = institution.date_signature_arrete or datetime.now()
    
    story.append(Paragraph(f"<b>ARRÊTÉ MINISTÉRIEL {numero_arrete} DU {date_signature.strftime('%d/%m/%Y')}</b>", style_title))
    story.append(Paragraph(
        f"<b>PORTANT AGRÉMENT D'UNE FÉDÉRATION SPORTIVE NATIONALE</b>",
        style_title
    ))
    story.append(Spacer(1, 0.8*cm))
    
    # Préambule juridique
    story.append(Paragraph("<b>Le Ministre des Sports et Loisirs,</b>", style_body))
    story.append(Spacer(1, 0.3*cm))
    
    # Récupérer le nom et profil du ministre
    ministere = institution.institution_tutelle
    nom_ministre = "[NOM_DU_MINISTRE]"
    ministre_profil = None
    
    if ministere:
        ministre_membre = Membre.objects.filter(
            institution=ministere,
            fonction__designation__icontains='Ministre'
        ).select_related('personne').first()
        
        if ministre_membre and ministre_membre.personne:
            nom_ministre = f"{ministre_membre.personne.nom} {ministre_membre.personne.postnom} {ministre_membre.personne.prenom}".strip()
            try:
                # Récupérer le profil du Ministre via la relation inverse
                ministre_profil = ministre_membre.personne.profils_utilisateur.filter(
                    role='MINISTRE'
                ).first()
            except Exception as e:
                print(f"Erreur récupération profil ministre: {e}")
                ministre_profil = None
    
    visas = [
        "Vu la Constitution, telle que modifiée par la Loi n°11/002 du 20 janvier 2011, spécialement en son article 93 ;",
        "Vu la Loi n°11/023 du 24 décembre 2011 portant principes fondamentaux relatifs à l'organisation et à la promotion des activités physiques et sportives en République Démocratique du Congo ;",
        "Vu l'Ordonnance n°___ du ___ portant nomination des membres du Gouvernement ;",
        f"Vu la demande d'agrément introduite par la fédération concernée en date du {institution.date_demande_agrement.strftime('%d/%m/%Y') if institution.date_demande_agrement else '[DATE_DEMANDE]'} ;",
        f"Considérant l'avis technique favorable émis par le Secrétariat Général aux Sports et Loisirs après examen du dossier F03 référencé {institution.numero_dossier or '[NUMERO_DOSSIER]'} ;",
        "Considérant la nécessité et l'urgence ;",
    ]
    
    for visa in visas:
        story.append(Paragraph(visa, style_body))
    
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("<b>ARRÊTE :</b>", style_body))
    story.append(Spacer(1, 0.3*cm))
    
    # Articles
    disciplines_list = ", ".join([d.designation for d in institution.disciplines.all()]) if institution.disciplines.exists() else "[DISCIPLINE]"
    
    # Adresse complète
    adresse_complete = "—"
    province_nom = "—"
    if institution.adresses_contact.exists():
        adresse = institution.adresses_contact.first()
        if adresse.groupement_quartier:
            adresse_parts = []
            if adresse.avenue:
                adresse_parts.append(adresse.avenue)
            if adresse.numero:
                adresse_parts.append(f"N°{adresse.numero}")
            if adresse.groupement_quartier.designation:
                adresse_parts.append(adresse.groupement_quartier.designation)
            if adresse.groupement_quartier.secteur.territoire.designation:
                adresse_parts.append(adresse.groupement_quartier.secteur.territoire.designation)
            adresse_complete = ", ".join(adresse_parts) if adresse_parts else "—"
            
            if adresse.groupement_quartier.secteur.territoire.province_admin:
                province_nom = adresse.groupement_quartier.secteur.territoire.province_admin.designation
    
    articles = [
        f"<b>Article 1er :</b> Est agréée à titre {institution.get_type_agrement_sollicite_display().lower() if institution.type_agrement_sollicite else 'provisoire'}, pour une durée de {institution.duree_sollicitee} ans, l'association sportive sans but lucratif dénommée <b>{institution.nom_officiel}</b>, en sigle <b>{institution.sigle}</b>, ayant son siège social à {adresse_complete}, Province de {province_nom}.",
        
        f"<b>Article 2 :</b> La Fédération susmentionnée a pour mission l'organisation, la promotion et le développement de la discipline <b>{disciplines_list}</b> sur toute l'étendue du territoire national.",
        
        "<b>Article 3 :</b> Le Secrétaire Général aux Sports et Loisirs est chargé de l'exécution du présent Arrêté qui entre en vigueur à la date de sa signature.",
    ]
    
    for article in articles:
        story.append(Paragraph(article, style_article))
        story.append(Spacer(1, 0.3*cm))
    
    story.append(Spacer(1, 1*cm))
    
    # Signature
    story.append(Paragraph(
        f"Fait à Kinshasa, le {date_signature.strftime('%d/%m/%Y')}",
        ParagraphStyle('FaitA', parent=style_body, alignment=TA_RIGHT, fontSize=11)
    ))
    story.append(Spacer(1, 0.5*cm))
    
    # Signature du Ministre (depuis son profil) - redimensionnée automatiquement
    if ministre_profil and ministre_profil.signature_image:
        try:
            # Redimensionner la signature (max 4cm x 2cm)
            signature_buffer = redimensionner_image(ministre_profil.signature_image.path, 4, 2)
            if signature_buffer:
                signature_img = Image(signature_buffer, width=4*cm, height=2*cm)
                signature_img.hAlign = 'RIGHT'
                story.append(signature_img)
            else:
                print("Erreur: signature_buffer est None")
                story.append(Spacer(1, 1*cm))
        except Exception as e:
            print(f"Erreur signature: {e}")
            import traceback
            traceback.print_exc()
            story.append(Spacer(1, 1*cm))
    else:
        if not ministre_profil:
            print("Erreur: ministre_profil est None")
        elif not ministre_profil.signature_image:
            print("Erreur: signature_image est vide")
        story.append(Spacer(1, 1*cm))
    
    story.append(Paragraph(nom_ministre, style_signature))
    story.append(Paragraph("Ministre des Sports et Loisirs", style_signature))
    
    # Sceau du Ministère (depuis le profil du ministre) - redimensionné automatiquement
    if ministre_profil and ministre_profil.sceau_image:
        try:
            # Redimensionner le sceau (max 3cm x 3cm)
            sceau_buffer = redimensionner_image(ministre_profil.sceau_image.path, 3, 3)
            if sceau_buffer:
                sceau_img = Image(sceau_buffer, width=3*cm, height=3*cm)
                sceau_img.hAlign = 'RIGHT'
                story.append(Spacer(1, 0.3*cm))
                story.append(sceau_img)
        except Exception as e:
            print(f"Erreur sceau: {e}")
    
    story.append(Spacer(1, 1*cm))
    
    # QR Code de vérification
    verification_url = f"{settings.SITE_URL}/verifier-arrete/{institution.uid}/"
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(verification_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    
    qr_image = Image(qr_buffer, width=3*cm, height=3*cm)
    qr_image.hAlign = 'CENTER'
    story.append(qr_image)
    
    # Pied de page
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        f"<i>Scannez ce QR Code pour vérifier l'authenticité de cet arrêté</i>",
        ParagraphStyle('QRInfo', parent=style_body, fontSize=9, textColor=colors.grey, alignment=TA_CENTER)
    ))
    story.append(Paragraph(
        f"<i>Document généré électroniquement le {datetime.now().strftime('%d/%m/%Y à %H:%M')} - Code: {str(institution.uid)[:8].upper()}</i>",
        ParagraphStyle('Footer', parent=style_body, fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    ))
    
    # Construction du PDF
    doc.build(story)
    
    buffer.seek(0)
    return buffer


def sauvegarder_arrete(institution):
    """
    Génère et sauvegarde l'Arrêté Ministériel pour une institution.
    """
    from django.core.files.base import ContentFile
    
    if not institution.numero_arrete:
        institution.numero_arrete = generer_numero_arrete()
    
    pdf_buffer = generer_arrete_agrement(institution)
    
    # Nom du fichier: ARRETE_[SIGLE]_[ANNEE].pdf
    annee = datetime.now().year
    sigle_clean = institution.sigle.replace(' ', '_').replace('/', '_') if institution.sigle else institution.code
    filename = f"ARRETE_{sigle_clean}_{annee}.pdf"
    
    institution.document_arrete.save(
        filename,
        ContentFile(pdf_buffer.getvalue()),
        save=False
    )
    
    if not institution.date_signature_arrete:
        institution.date_signature_arrete = datetime.now()
    
    institution.save()
    
    return institution.document_arrete.path
