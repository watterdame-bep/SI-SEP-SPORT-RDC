"""
Commande pour créer les disciplines sportives de base
"""
from django.core.management.base import BaseCommand
from gouvernance.models.discipline import DisciplineSport


class Command(BaseCommand):
    help = 'Crée les disciplines sportives de base pour la RDC'

    def handle(self, *args, **options):
        disciplines = [
            {'code': 'FOOT', 'designation': 'Football', 'ordre': 1},
            {'code': 'BASKET', 'designation': 'Basketball', 'ordre': 2},
            {'code': 'VOLLEY', 'designation': 'Volleyball', 'ordre': 3},
            {'code': 'HAND', 'designation': 'Handball', 'ordre': 4},
            {'code': 'ATHL', 'designation': 'Athlétisme', 'ordre': 5},
            {'code': 'BOXE', 'designation': 'Boxe', 'ordre': 6},
            {'code': 'JUDO', 'designation': 'Judo', 'ordre': 7},
            {'code': 'KARATE', 'designation': 'Karaté', 'ordre': 8},
            {'code': 'TENNIS', 'designation': 'Tennis', 'ordre': 9},
            {'code': 'NATATION', 'designation': 'Natation', 'ordre': 10},
        ]

        created_count = 0
        for disc_data in disciplines:
            disc, created = DisciplineSport.objects.get_or_create(
                code=disc_data['code'],
                defaults={
                    'designation': disc_data['designation'],
                    'ordre': disc_data['ordre'],
                    'actif': True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Discipline créée: {disc.designation}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'- Discipline existante: {disc.designation}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n{created_count} discipline(s) créée(s) sur {len(disciplines)}')
        )
