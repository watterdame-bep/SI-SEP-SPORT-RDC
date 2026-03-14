"""
Management command pour remplir les types d'infrastructure.
"""
from django.core.management.base import BaseCommand
from infrastructures.models import TypeInfrastructure


class Command(BaseCommand):
    help = 'Remplit la base de données avec les types d\'infrastructure'

    def handle(self, *args, **options):
        types_data = [
            {'designation': 'Stade Omnisports', 'code': 'STAD'},
            {'designation': 'Terrain de Football', 'code': 'FOOT'},
            {'designation': 'Terrain de Basketball', 'code': 'BASK'},
            {'designation': 'Terrain de Volleyball', 'code': 'VOLL'},
            {'designation': 'Terrain de Tennis', 'code': 'TENN'},
            {'designation': 'Piscine Olympique', 'code': 'PISC'},
            {'designation': 'Salle de Boxe', 'code': 'BOXA'},
            {'designation': 'Salle d\'Athlétisme', 'code': 'ATHL'},
            {'designation': 'Salle de Judo', 'code': 'JUDO'},
            {'designation': 'Salle de Lutte', 'code': 'LUTT'},
            {'designation': 'Salle de Badminton', 'code': 'BADM'},
            {'designation': 'Salle de Handball', 'code': 'HAND'},
            {'designation': 'Salle de Ping-Pong', 'code': 'PING'},
            {'designation': 'Terrain de Cricket', 'code': 'CRIC'},
            {'designation': 'Terrain de Rugby', 'code': 'RUGB'},
            {'designation': 'Salle de Musculation', 'code': 'MUSC'},
            {'designation': 'Salle de Danse', 'code': 'DANS'},
            {'designation': 'Salle de Karaté', 'code': 'KARA'},
            {'designation': 'Salle de Taekwondo', 'code': 'TAEK'},
            {'designation': 'Terrain de Golf', 'code': 'GOLF'},
        ]
        
        created_count = 0
        for type_data in types_data:
            obj, created = TypeInfrastructure.objects.get_or_create(
                code=type_data['code'],
                defaults={'designation': type_data['designation']}
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Créé: {obj.designation} ({obj.code})')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'✗ Existe déjà: {obj.designation} ({obj.code})')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n{created_count} type(s) d\'infrastructure créé(s) avec succès!')
        )
