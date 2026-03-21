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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT, TA_LEFT
from reportlab.pdfgen import canvas
import qrcode
from PIL import Image as PILImage


def generer_numero_arrete(annee=None):
    from gouvernance.models import Institution
    if annee is None:
        annee = datetime.now().year
    count = Institution.objects.filter(
        numero_arrete__contains=f'/MIN/SL/{annee}',
        statut_signature='SIGNE'
    ).count()
    return f"N°{count + 1:03d}/MIN/SL/{annee}"


def redimensionner_image(image_path, max_width_cm, max_height_cm):
    try:
        DPI = 150
        img = PILImage.open(image_path)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        # Calculer la taille cible en pixels à 150 DPI
        max_width_px = int(max_width_cm / 2.54 * DPI)
        max_height_px = int(max_height_cm / 2.54 * DPI)
        ratio = min(max_width_px / img.width, max_height_px / img.height)
        if ratio < 1:
            img = img.resize((int(img.width * ratio), int(img.height * ratio)), PILImage.Resampling.LANCZOS)
        output = BytesIO()
        img.save(output, format='PNG', dpi=(DPI, DPI))
        output.seek(0)
        return output
    except Exception as e:
        print(f"Erreur redimensionnement image: {e}")
        return None


def _get_ministre_profil():
    """Récupère le profil du Ministre actif dans le système."""
    try:
        from core.models import ProfilUtilisateur
        return ProfilUtilisateur.objects.filter(
            role='MINISTRE',
            user__is_active=True
        ).select_related('user').first()
    except Exception as e:
        print(f"Erreur récupération profil ministre: {e}")
        return None


def _get_ministre_nom(ministre_profil):
    """Retourne le nom complet du ministre depuis son profil."""
    if not ministre_profil:
        return "[NOM DU MINISTRE]"
    try:
        agent = getattr(ministre_profil, 'agent', None)
        if agent and agent.personne:
            p = agent.personne
            parts = [p.prenom, p.nom, p.postnom]
            return " ".join(x for x in parts if x).strip() or "[NOM DU MINISTRE]"
    except Exception:
        pass
    user = ministre_profil.user
    full = f"{user.first_name} {user.last_name}".strip()
    return full if full else user.username


def generer_arrete_agrement(institution):
    """Génère le PDF de l'Arrêté Ministériel d'Agrément."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=0.8*cm,
        bottomMargin=1.5*cm,
    )

    styles = getSampleStyleSheet()
    BLUE = colors.HexColor('#0036ca')
    DARK = colors.HexColor('#1a1a2e')
    GREY = colors.HexColor('#6b7280')

    s_header = ParagraphStyle('Header', fontSize=10, textColor=BLUE,
                               alignment=TA_CENTER, fontName='Helvetica-Bold', spaceAfter=2)
    s_title = ParagraphStyle('Title', fontSize=13, textColor=DARK,
                              alignment=TA_CENTER, fontName='Helvetica-Bold',
                              spaceAfter=6, spaceBefore=6)
    s_body = ParagraphStyle('Body', fontSize=10.5, alignment=TA_JUSTIFY,
                             spaceAfter=8, leading=16, fontName='Helvetica')
    s_article = ParagraphStyle('Article', fontSize=10.5, alignment=TA_JUSTIFY,
                                spaceAfter=8, leading=16, leftIndent=0.8*cm, fontName='Helvetica')
    s_right = ParagraphStyle('Right', fontSize=10.5, alignment=TA_RIGHT, fontName='Helvetica')
    s_right_bold = ParagraphStyle('RightBold', fontSize=10.5, alignment=TA_RIGHT,
                                   fontName='Helvetica-Bold')

    story = []

    # ── En-tête : logo + texte officiel ──────────────────────────────────────
    logo_path = os.path.join(settings.BASE_DIR, 'public', 'assets', 'images', 'logo-rdc.png')
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=2.2*cm, height=2.2*cm)
            header_row = [[
                logo,
                Paragraph(
                    "REPUBLIQUE DEMOCRATIQUE DU CONGO<br/>"
                    "<b>MINISTERE DES SPORTS ET LOISIRS</b><br/>"
                    "<font size='8' color='grey'>Ministere des Sports et Loisirs</font>",
                    ParagraphStyle('HeaderText', fontSize=10, textColor=BLUE,
                                   alignment=TA_CENTER, fontName='Helvetica-Bold', leading=14)
                )
            ]]
            t = Table(header_row, colWidths=[2.5*cm, 12*cm])
            t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                   ('ALIGN', (0, 0), (0, 0), 'CENTER')]))
            story.append(t)
        except Exception:
            story.append(Paragraph("REPUBLIQUE DEMOCRATIQUE DU CONGO", s_header))
            story.append(Paragraph("MINISTERE DES SPORTS ET LOISIRS", s_header))
    else:
        story.append(Paragraph("REPUBLIQUE DEMOCRATIQUE DU CONGO", s_header))
        story.append(Paragraph("MINISTERE DES SPORTS ET LOISIRS", s_header))

    story.append(Spacer(1, 0.4*cm))
    story.append(HRFlowable(width="100%", thickness=2, color=BLUE, spaceAfter=0.4*cm))

    # ── Titre ────────────────────────────────────────────────────────────────
    numero_arrete = institution.numero_arrete or generer_numero_arrete()
    date_signature = institution.date_signature_arrete or datetime.now()

    story.append(Paragraph(f"ARRETE MINISTERIEL {numero_arrete}", s_title))
    story.append(Paragraph(
        f"DU {date_signature.strftime('%d %B %Y').upper()}",
        ParagraphStyle('DateTitle', fontSize=11, alignment=TA_CENTER,
                       fontName='Helvetica-Bold', textColor=GREY, spaceAfter=4)
    ))
    story.append(Paragraph(
        "PORTANT AGREMENT D'UNE FEDERATION SPORTIVE NATIONALE",
        ParagraphStyle('SubTitle', fontSize=11, alignment=TA_CENTER,
                       fontName='Helvetica-Bold', textColor=DARK, spaceAfter=8)
    ))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0'),
                             spaceAfter=0.5*cm))

    # ── Ministre ─────────────────────────────────────────────────────────────
    ministre_profil = _get_ministre_profil()
    nom_ministre = _get_ministre_nom(ministre_profil)

    # ── Preambule ────────────────────────────────────────────────────────────
    story.append(Paragraph("<b>Le Ministre des Sports et Loisirs,</b>", s_body))
    story.append(Spacer(1, 0.2*cm))

    date_demande = institution.date_demande_agrement.strftime('%d/%m/%Y') if institution.date_demande_agrement else '[DATE_DEMANDE]'
    numero_dossier = institution.numero_dossier or '[NUMERO_DOSSIER]'

    visas = [
        "Vu la Constitution, telle que modifiee par la Loi n11/002 du 20 janvier 2011, specialement en son article 93 ;",
        "Vu la Loi n11/023 du 24 decembre 2011 portant principes fondamentaux relatifs a l'organisation et a la promotion des activites physiques et sportives en Republique Democratique du Congo ;",
        "Vu l'Ordonnance portant nomination des membres du Gouvernement ;",
        f"Vu la demande d'agrement introduite par la federation concernee en date du {date_demande} ;",
        f"Considerant l'avis technique favorable emis par le Secretariat General aux Sports et Loisirs apres examen du dossier reference {numero_dossier} ;",
        "Considerant la necessite et l'urgence ;",
    ]
    for visa in visas:
        story.append(Paragraph(visa, s_body))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<b>ARRETE :</b>", s_body))
    story.append(Spacer(1, 0.2*cm))

    # ── Articles ─────────────────────────────────────────────────────────────
    disciplines_list = ", ".join([d.designation for d in institution.disciplines.all()]) or "[DISCIPLINE]"

    adresse_complete = "—"
    province_nom = "—"
    if institution.adresses_contact.exists():
        adresse = institution.adresses_contact.first()
        if adresse.groupement_quartier:
            parts = []
            if adresse.avenue:
                parts.append(adresse.avenue)
            if adresse.numero:
                parts.append(f"N{adresse.numero}")
            if adresse.groupement_quartier.designation:
                parts.append(adresse.groupement_quartier.designation)
            if adresse.groupement_quartier.secteur.territoire.designation:
                parts.append(adresse.groupement_quartier.secteur.territoire.designation)
            adresse_complete = ", ".join(parts) if parts else "—"
            if adresse.groupement_quartier.secteur.territoire.province_admin:
                province_nom = adresse.groupement_quartier.secteur.territoire.province_admin.designation

    type_agrement = institution.get_type_agrement_sollicite_display().lower() if institution.type_agrement_sollicite else "provisoire"

    articles = [
        (f"<b>Article 1er :</b> Est agreee a titre <b>{type_agrement}</b>, pour une duree de "
         f"<b>{institution.duree_sollicitee} ans</b>, l'association sportive sans but lucratif denommee "
         f"<b>{institution.nom_officiel}</b>, en sigle <b>{institution.sigle}</b>, ayant son siege social a "
         f"{adresse_complete}, Province de {province_nom}."),
        (f"<b>Article 2 :</b> La Federation susmentionnee a pour mission l'organisation, la promotion et le "
         f"developpement de la discipline <b>{disciplines_list}</b> sur toute l'etendue du territoire national."),
        ("<b>Article 3 :</b> Le Secretaire General aux Sports et Loisirs est charge de l'execution du present "
         "Arrete qui entre en vigueur a la date de sa signature."),
    ]
    for article in articles:
        story.append(Paragraph(article, s_article))
        story.append(Spacer(1, 0.2*cm))

    story.append(Spacer(1, 0.8*cm))

    # ── Zone bas : QR gauche + signature droite ───────────────────────────────
    verification_url = f"{settings.SITE_URL}/verifier-arrete/{institution.uid}/"
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(verification_url)
    qr.make(fit=True)
    qr_pil = qr.make_image(fill_color="black", back_color="white")
    qr_buf = BytesIO()
    qr_pil.save(qr_buf, format='PNG')
    qr_buf.seek(0)

    # Colonne droite : signature + nom ministre
    right_col = []
    right_col.append(Paragraph(
        f"Fait a Kinshasa, le {date_signature.strftime('%d/%m/%Y')}",
        s_right
    ))
    right_col.append(Spacer(1, 0.2*cm))
    right_col.append(Paragraph("<b>Le Ministre des Sports et Loisirs</b>", s_right_bold))
    right_col.append(Spacer(1, 0.2*cm))
    if ministre_profil and ministre_profil.signature_image:
        try:
            sig_buf2 = redimensionner_image(ministre_profil.signature_image.path, 5, 2.5)
            if sig_buf2:
                sig_img2 = Image(sig_buf2, width=5*cm, height=2.5*cm)
                sig_img2.hAlign = 'RIGHT'
                right_col.append(sig_img2)
            else:
                right_col.append(Spacer(1, 2.5*cm))
        except Exception as e:
            print(f"Erreur signature bas: {e}")
            right_col.append(Spacer(1, 2.5*cm))
    else:
        right_col.append(Spacer(1, 1.5*cm))
        right_col.append(HRFlowable(width="60%", thickness=0.5, color=DARK))
    right_col.append(Spacer(1, 0.2*cm))
    right_col.append(Paragraph(f"<b>{nom_ministre}</b>", s_right_bold))

    bottom_table = Table(
        [[Image(qr_buf, width=2.8*cm, height=2.8*cm), right_col]],
        colWidths=[3.5*cm, 11.5*cm]
    )
    bottom_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    story.append(bottom_table)

    doc.build(story)
    buffer.seek(0)
    return buffer


def sauvegarder_arrete(institution):
    from django.core.files.base import ContentFile
    if not institution.numero_arrete:
        institution.numero_arrete = generer_numero_arrete()
    pdf_buffer = generer_arrete_agrement(institution)
    annee = datetime.now().year
    sigle_clean = institution.sigle.replace(' ', '_').replace('/', '_') if institution.sigle else institution.code
    filename = f"ARRETE_{sigle_clean}_{annee}.pdf"
    institution.document_arrete.save(filename, ContentFile(pdf_buffer.getvalue()), save=False)
    if not institution.date_signature_arrete:
        institution.date_signature_arrete = datetime.now()
    institution.save()
    return institution.document_arrete.path
