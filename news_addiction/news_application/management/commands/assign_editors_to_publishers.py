from django.core.management.base import BaseCommand
from datetime import date
from news_application.models import Roles, User, Publisher

class Command(BaseCommand):
    """Create tests users for the news application
       Usage:
       python manage.py create_test_users
       To overwrite existing users:
       python manage.py create_test_users --skip-existing
    """
    help = 'Create test users for the news application'

 
    def handle(self, *args, **options):
        """
        Create default users for the news application
        """
        
        # Define default users to create
        test_editors = [
       
            {
                'username': 'test_editor_1',
            },
            {
                'username': 'test_editor_2',
            },
           
        ]

        test_publishers = [
       
            {
                'name': 'The Star',
            },
            {
                'name': 'The Citizen',
            },
        ]

 
        assigned_count = 0
        skipped_count = 0

        for data in test_publishers:
            name = data['name']
            
            # Check if user already exists
            publisher = Publisher.objects.filter(name=name).first()
            if publisher:
                for editor_data in test_editors:
                    username = editor_data['username']
                    try:
                        publisher.editors.add(
                            User.objects.get(username=username))

                        self.stdout.write(
                                self.style.SUCCESS(
                                    f'Successfully assigned user "{username}" '
                                    f'to publisher "{name}"'
                                )
                            )
                        assigned_count += 1
                        
                    except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(
                                    f'Error assigning user "{username}": {str(e)}'
                                )
                            )
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: Assigned {assigned_count} users, '
                f'skipped {skipped_count} users'
            )
        )