# -*- coding: utf-8 -*-
"""
Service d'envoi d'e-mails pour les billets SI-SEP Sport RDC
"""
import smtplib
import ssl
import base64
import qrcode
from io import BytesIO
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from django.conf import settings


class EmailService:
    """Service pour l'envoi d'e-mails contenant les billets avec QR codes"""

    def __init__(self):
        self.smtp_server = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'EMAIL_PORT', 587)
        self.smtp_username = getattr(settings, 'EMAIL_HOST_USER', '')
        self.smtp_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        self.sender_name = getattr(settings, 'EMAIL_SENDER_NAME', 'SI-SEP Sport RDC')
        self.site_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')

    def _generer_qr_base64(self, ticket_uid):
        """Génère un QR code en base64 pour un ticket"""
        qr_url = f"{self.site_url}/verify/ticket/{ticket_uid}/"
        qr = qrcode.QRCode(version=1, box_size=6, border=2)
        qr.add_data(qr_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def envoyer_billet_email(self, email_destinataire, nom_destinataire, vente, tickets):
        """
        Envoie un e-mail avec les billets et QR codes en base64 embarqués.
        """
        try:
            msg = MIMEMultipart('mixed')
            msg['From'] = formataddr((self.sender_name, self.smtp_username))
            msg['To'] = formataddr((nom_destinataire, email_destinataire))
            msg['Subject'] = f"Vos billets SI-SEP Sport RDC — Réf. {vente.reference_paiement}"

            # Construire les données de chaque ticket
            tickets_data = []
            for ticket in tickets:
                qr_b64 = self._generer_qr_base64(str(ticket.uid))
                try:
                    match_nom = str(ticket.evenement_zone.evenement.titre)
                    zone_nom = ticket.evenement_zone.zone_stade.nom
                    date_match = ticket.evenement_zone.evenement.date_evenement.strftime('%d/%m/%Y %H:%M')
                    lieu = ticket.evenement_zone.evenement.infrastructure.nom
                except Exception:
                    match_nom = "Match"
                    zone_nom = "Tribune"
                    date_match = ""
                    lieu = ""

                tickets_data.append({
                    'uid': str(ticket.uid),
                    'numero': ticket.numero_billet.upper() if ticket.numero_billet else str(ticket.uid)[:8].upper(),
                    'qr_b64': qr_b64,
                    'match_nom': match_nom,
                    'zone_nom': zone_nom,
                    'date_match': date_match,
                    'lieu': lieu,
                })

            html_content = self._generer_html(vente, tickets_data, nom_destinataire)
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))

            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            return {
                'success': True,
                'message': f'E-mail envoyé à {email_destinataire}',
                'tickets_count': len(tickets)
            }

        except Exception as e:
            import traceback
            print(f"ERREUR EMAIL: {e}")
            print(traceback.format_exc())
            return {
                'success': False,
                'message': f"Erreur envoi e-mail: {str(e)}",
                'error': str(e)
            }

    def _generer_html(self, vente, tickets_data, nom_destinataire):
        """Génère le HTML de l'e-mail avec les billets"""

        tickets_html = ""
        for i, t in enumerate(tickets_data, 1):
            tickets_html += f"""
            <div style="border:2px solid #0036ca;border-radius:8px;padding:20px;margin:16px 0;">
                <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                        <td style="vertical-align:top;padding-right:20px;">
                            <h3 style="color:#0036ca;margin:0 0 12px 0;font-size:16px;text-transform:uppercase;">
                                &#127915; Billet #{i}
                            </h3>
                            <table cellpadding="4" cellspacing="0">
                                <tr>
                                    <td style="color:#666;font-size:13px;font-weight:bold;white-space:nowrap;">N° Billet:</td>
                                    <td style="color:#333;font-size:13px;font-family:monospace;">{t['numero']}</td>
                                </tr>
                                <tr>
                                    <td style="color:#666;font-size:13px;font-weight:bold;">Match:</td>
                                    <td style="color:#111;font-size:13px;">{t['match_nom']}</td>
                                </tr>
                                <tr>
                                    <td style="color:#666;font-size:13px;font-weight:bold;">Date:</td>
                                    <td style="color:#333;font-size:13px;">{t['date_match']}</td>
                                </tr>
                                <tr>
                                    <td style="color:#666;font-size:13px;font-weight:bold;">Lieu:</td>
                                    <td style="color:#333;font-size:13px;">{t['lieu']}</td>
                                </tr>
                                <tr>
                                    <td style="color:#666;font-size:13px;font-weight:bold;">Tribune:</td>
                                    <td style="color:#333;font-size:13px;">{t['zone_nom']}</td>
                                </tr>
                            </table>
                        </td>
                        <td style="vertical-align:top;text-align:center;width:140px;">
                            <img src="data:image/png;base64,{t['qr_b64']}"
                                 alt="QR Code Billet #{i}"
                                 width="130" height="130"
                                 style="display:block;margin:0 auto;border:1px solid #ddd;">
                            <p style="font-size:11px;color:#666;margin:6px 0 0 0;">Scannez à l'entrée</p>
                        </td>
                    </tr>
                </table>
            </div>
            """

        # Infos vente
        ref = getattr(vente, 'reference_paiement', '')
        nom_acheteur = getattr(vente, 'nom_acheteur', nom_destinataire)
        telephone = getattr(vente, 'telephone_acheteur', '')
        montant = getattr(vente, 'montant_total', getattr(vente, 'montantvise', ''))

        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Vos billets SI-SEP Sport RDC</title>
</head>
<body style="margin:0;padding:0;background:#f8f9fa;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8f9fa;">
<tr><td align="center" style="padding:20px;">
<table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;max-width:600px;width:100%;">

    <!-- Header -->
    <tr>
        <td style="background:linear-gradient(135deg,#0036ca,#002a9e);padding:32px 24px;text-align:center;border-radius:8px 8px 0 0;">
            <div style="font-size:48px;margin-bottom:8px;">&#127942;</div>
            <h1 style="color:#FDE015;margin:0;font-size:24px;text-transform:uppercase;letter-spacing:1px;">
                Paiement Réussi !
            </h1>
            <p style="color:rgba(255,255,255,0.85);margin:8px 0 0 0;font-size:15px;">
                Vos billets sont prêts — SI-SEP Sport RDC
            </p>
        </td>
    </tr>

    <!-- Body -->
    <tr>
        <td style="padding:24px;">

            <p style="font-size:15px;color:#333;margin:0 0 20px 0;">
                Bonjour <strong>{nom_destinataire}</strong>,<br>
                Merci pour votre achat. Voici vos billets pour le match.
            </p>

            <!-- Récapitulatif commande -->
            <div style="background:#f8f9fa;border-left:4px solid #0036ca;padding:16px;border-radius:4px;margin-bottom:24px;">
                <table cellpadding="4" cellspacing="0" width="100%">
                    <tr>
                        <td style="color:#666;font-size:13px;font-weight:bold;">Référence:</td>
                        <td style="color:#333;font-size:13px;font-family:monospace;">{ref}</td>
                    </tr>
                    <tr>
                        <td style="color:#666;font-size:13px;font-weight:bold;">Nom:</td>
                        <td style="color:#333;font-size:13px;">{nom_acheteur}</td>
                    </tr>
                    <tr>
                        <td style="color:#666;font-size:13px;font-weight:bold;">Téléphone:</td>
                        <td style="color:#333;font-size:13px;">{telephone}</td>
                    </tr>
                    <tr>
                        <td style="color:#666;font-size:13px;font-weight:bold;">Montant payé:</td>
                        <td style="color:#0036ca;font-size:13px;font-weight:bold;">{montant} CDF</td>
                    </tr>
                </table>
            </div>

            <!-- Billets -->
            <h2 style="color:#0036ca;font-size:18px;margin:0 0 8px 0;text-transform:uppercase;">
                Vos Billets ({len(tickets_data)})
            </h2>
            <p style="color:#666;font-size:13px;margin:0 0 16px 0;">
                Présentez le QR code à l'entrée du stade (sur écran ou imprimé).
            </p>

            {tickets_html}

            <!-- Instructions -->
            <div style="background:#fff8e1;border:1px solid #FDE015;border-radius:6px;padding:16px;margin-top:24px;">
                <h3 style="color:#0036ca;margin:0 0 10px 0;font-size:14px;text-transform:uppercase;">
                    Instructions importantes
                </h3>
                <ul style="margin:0;padding-left:20px;color:#333;font-size:13px;line-height:1.8;">
                    <li>Arrivez au stade <strong>30 minutes avant</strong> le match</li>
                    <li>Présentez votre QR code à l'entrée</li>
                    <li>Munissez-vous d'une pièce d'identité valide</li>
                    <li>Chaque billet n'est valable qu'<strong>une seule fois</strong></li>
                </ul>
            </div>

        </td>
    </tr>

    <!-- Footer -->
    <tr>
        <td style="text-align:center;padding:20px;color:#999;font-size:12px;border-top:1px solid #eee;">
            <p style="margin:0;">&#169; 2026 SI-SEP Sport RDC — Ministère des Sports</p>
            <p style="margin:4px 0 0 0;">Cet e-mail est généré automatiquement, merci de ne pas y répondre.</p>
        </td>
    </tr>

</table>
</td></tr>
</table>
</body>
</html>"""


# Instance globale
email_service = EmailService()
