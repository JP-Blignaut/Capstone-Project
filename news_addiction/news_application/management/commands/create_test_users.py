import os
from django.core.management.base import BaseCommand
from datetime import date
from news_application.models import Roles, User
from django.core.files import File


class Command(BaseCommand):
    """Create tests users for the news application
       Usage:
       python manage.py create_test_users
       To overwrite existing users:
       python manage.py create_test_users --skip-existing
    """
    image_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "images")
    help = 'Create test users for the news application'

    def add_arguments(self, parser):
        parser.add_argument(
            '--overwrite-existing',
            action='store_true',
            help='Overwrite existing users',
        )

    def handle(self, *args, **options):
        """
        Create default users for the news application
        """
        
        # Define default users to create
        test_users = [
            {
                'username': 'admin',
                'email': 'admin@example.com',
                'password': 'admin',
                'display_name': 'System Administrator',
                'phone_number': '+27123456789',
                'date_of_birth': date(1990, 1, 1),
                'role': Roles.EDITOR,
                'is_staff': True,
                'is_superuser': True,
                'profile_picture': None,
                'biography': None,
            },
            {
                'username': 'test_editor_1',
                'email': 'test_editor_1@example.com',
                'password': 'password123',
                'display_name': 'Test Editor 1',
                'phone_number': '+27123456790',
                'date_of_birth': date(1985, 5, 15),
                'role': Roles.EDITOR,
                'is_staff': False,
                'is_superuser': False,
                'profile_picture': None,
                'biography': None,
            },
            {
                'username': 'test_editor_2',
                'email': 'test_editor_2@example.com',
                'password': 'password123',
                'display_name': 'Test Editor 2',
                'phone_number': '+27123456790',
                'date_of_birth': date(1985, 5, 15),
                'role': Roles.EDITOR,
                'is_staff': False,
                'is_superuser': False,
                'profile_picture': None,
                'biography': None,
            },
            {
                'username': 'test_journalist_1',
                'email': 'test_journalist_1@example.com',
                'password': 'password123',
                'display_name': 'Test Journalist 1',
                'phone_number': '+27123456791',
                'date_of_birth': date(1988, 3, 20),
                'role': Roles.JOURNALIST,
                'is_staff': False,
                'is_superuser': False,
                'profile_picture': os.path.join(self.image_dir,
                                                'Eben.jpeg'),
                'biography': ("World class enforcer and back to back world "
                              "cup winner"),
            },
            {
                'username': 'test_journalist_2',
                'email': 'test_journalist_2@example.com',
                'password': 'password123',
                'display_name': 'Test Journalist 2',
                'phone_number': '+27123456791',
                'date_of_birth': date(1988, 3, 20),
                'role': Roles.JOURNALIST,
                'is_staff': False,
                'is_superuser': False,
                'profile_picture': os.path.join(self.image_dir,
                                                'Musk.jpeg'),
                'biography': "Genius and the world's richest man",
            },
            {
                'username': 'test_reader_1',
                'email': 'test_reader_1@example.com',
                'password': 'password123',
                'display_name': 'Test Reader 1',
                'phone_number': '+27123456792',
                'date_of_birth': date(1995, 7, 10),
                'role': Roles.READER,
                'is_staff': False,
                'is_superuser': False,
                'profile_picture': None,
                'biography': None,
            },
            {
                'username': 'test_reader_2',
                'email': 'test_reader_2@example.com',
                'password': 'password123',
                'display_name': 'Test Reader 2',
                'phone_number': '+27123456792',
                'date_of_birth': date(1995, 7, 10),
                'role': Roles.READER,
                'is_staff': False,
                'is_superuser': False,
                'profile_picture': None,
                'biography': None,
            },
        ]

        created_count = 0
        skipped_count = 0

        for user_data in test_users:
            username = user_data['username']
            
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                if not options['overwrite_existing']:
                    self.stdout.write(
                        self.style.WARNING(
                            f'User "{username}" already exists, skipping...'
                        )
                    )
                    skipped_count += 1
                    continue

            # Create the user
            try:
                # Build user creation arguments dynamically
                user_args = {
                    'username': user_data['username'],
                    'email': user_data['email'],
                    'password': user_data['password'],
                    'display_name': user_data['display_name'],
                    'phone_number': user_data['phone_number'],
                    'date_of_birth': user_data['date_of_birth'],
                    'role': user_data['role'],
                    'is_staff': user_data['is_staff'],
                    'is_superuser': user_data['is_superuser'],
                }

                # Add optional fields if they exist and are not None
                optional_fields = []

                for field in optional_fields:
                    if field in user_data and user_data[field] is not None:
                        user_args[field] = user_data[field]

                # Handle profile picture separately
                if (user_data.get('profile_picture') and
                        os.path.exists(user_data['profile_picture'])):
                    profile_pic_path = user_data['profile_picture']
                    profile_pic_filename = os.path.basename(profile_pic_path)
                    with open(profile_pic_path, 'rb') as profile_pic_file:
                        user_args['profile_picture'] = File(
                            profile_pic_file, name=profile_pic_filename)
                        User.objects.create_user(**user_args)
                else:
                    User.objects.create_user(**user_args)

                if (user_data['role'] == Roles.JOURNALIST) and (
                        user_data.get('biography')):
                    print("Updating biography for journalist:", username)
                    journalist = User.objects.get(username=username)
                    journalist.journalist_profile.biography = user_data[
                        'biography']
                    journalist.journalist_profile.save() 
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created user "{username}" '
                        f'with role "{user_data["role"]}"'
                    )
                )
                created_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error creating user "{username}": {str(e)}'
                    )
                )

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: Created {created_count} users, '
                f'skipped {skipped_count} users'
            )
        )