from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from infrastructures.models import Ticket, Vente
import json
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Nettoie les réservations de tickets expirées (plus de 15 minutes)'

    def handle(self, *args, **options):
        self.stdout.write('Début du nettoyage des réservations expirées...')
        
        # Calculer la date limite (il y a 15 minutes)
        date_limite = timezone.now() - timedelta(minutes=15)
        
        # Trouver les tickets EN_RESERVATION plus anciens que 15 minutes
        tickets_expires = Ticket.objects.filter(
            statut='EN_RESERVATION',
            date_creation__lt=date_limite
        )
        
        count_tickets = tickets_expires.count()
        
        if count_tickets > 0:
            # Libérer les tickets expirés
            count_libere = tickets_expires.update(statut='DISPONIBLE', vente=None)
            
            self.stdout.write(self.style.SUCCESS(
                f'{count_libere} tickets expirés ont été libérés et retournés au statut DISPONIBLE'
            ))
            
            # Marquer les ventes associées comme expirées si elles existent
            ventes_uids = tickets_expires.values_list('vente__uid', flat=True).distinct()
            ventes_uids = [uid for uid in ventes_uids if uid]  # Filtrer les None
            
            if ventes_uids:
                ventes = Vente.objects.filter(uid__in=ventes_uids)
                count_ventes = ventes.count()
                
                for vente in ventes:
                    notes_data = json.loads(vente.notes) if vente.notes else {}
                    notes_data['statut_paiement'] = 'EXPIRE'
                    notes_data['date_expiration'] = timezone.now().isoformat()
                    notes_data['raison_expiration'] = 'Timeout de 15 minutes dépassé'
                    vente.notes = json.dumps(notes_data)
                    vente.save()
                
                self.stdout.write(self.style.WARNING(
                    f'{count_ventes} ventes marquées comme EXPIREES'
                ))
            
            logger.info(f'Nettoyage automatique: {count_libere} tickets libérés, {count_ventes} ventes expirées')
        else:
            self.stdout.write(self.style.SUCCESS('Aucun ticket expiré à nettoyer'))
        
        self.stdout.write('Nettoyage des réservations expirées terminé.')
