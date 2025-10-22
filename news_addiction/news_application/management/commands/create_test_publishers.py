import os
from django.core.management.base import BaseCommand
from datetime import date
from news_application.models import Roles, User, Publisher
from django.conf import settings
from django.core.files import File




class Command(BaseCommand):
    """Create test publishers users for the news application
       Usage:
       python manage.py create_test_publishers
       To overwrite existing publishers:
       python manage.py create_test_publishers --skip-existing
    """
    help = 'Create test publishers users for the news application'

    image_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "images")


    def add_arguments(self, parser):
        parser.add_argument(
            '--overwrite-existing',
            action='store_true',
            help='Overwrite existing users',
        )

    def handle(self, *args, **options):
        """
        Create default publishers for the news application
        """
        
        # Define default users to create
        test_publishers = [
            {
                'name': 'The Star',
                'description': 'The Star news publisher',
                'website': 'https://www.thestar.co.za',
                'email': 'thestar@example.com',
                'logo_path': os.path.join(self.image_dir, 'logo_the_star.png')
             
            },
            {
                'name': 'The Citizen',
                'description': 'The Citizen news publisher',
                'website': 'https://www.citizen.co.za/',
                'email': 'thecitizen@example.com',
                'logo_path': os.path.join(self.image_dir,
                                          'logo_the_citizen.png')
            },
        ]

        created_count = 0
        skipped_count = 0

        for publisher_data in test_publishers:
            name = publisher_data['name']
            
            # Check if user already exists
           
            if Publisher.objects.filter(name=name).exists():
                if not options['overwrite_existing']:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Publisher "{name}" already exists, skipping...'
                        )
                    )
                    skipped_count += 1
                    continue

            # Create the publisher
            try:
                print(publisher_data['logo_path'])
                if os.path.exists(publisher_data['logo_path']):
                    logo_path = publisher_data['logo_path']
                    logo_filename = os.path.basename(logo_path)
                    with open(logo_path, 'rb') as logo_file:
                        publisher = Publisher.objects.create(
                            name=publisher_data['name'],
                            description=publisher_data['description'],
                            website=publisher_data['website'],
                            email=publisher_data['email'],
                            logo=File(logo_file, name=logo_filename)
                        )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Successfully created publisher '
                                f'"{publisher_data["name"]}"'
                            )
                        )
                        created_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error creating publisher '
                        f'{publisher_data["name"]}: {str(e)}'
                    )
                )

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: Created {created_count} publishers, '
                f'skipped {skipped_count} publishers'
            )
        )