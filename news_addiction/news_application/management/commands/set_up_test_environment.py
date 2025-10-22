from django.core.management.base import BaseCommand
from datetime import date
from news_application.models import Roles, User
from django.core.management import call_command



class Command(BaseCommand):
    """
    Create test users for the news application, creates test
    publishers and assign editors to publishers. This effectively automates
    everthing that would need to be done in the custom admin console to test
    the application.

    """
    help = "Create test users for the news application, creates test "
    "publishers and assign editors to publishers"

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite-existing",
            action="store_true",
            help="Overwrite existing users",
        )

    def handle(self, *args, **options):
        # Create test users:
        self.stdout.write(self.style.WARNING("Creating test users..."))
        call_command("create_test_users",
                     overwrite_existing=options['overwrite_existing'])

        self.stdout.write(self.style.WARNING("Creating test publishers..."))
        call_command("create_test_publishers",
                     overwrite_existing=options['overwrite_existing'])

        self.stdout.write(self.style.WARNING(
            "Assigning editors to publishers..."))
        call_command("assign_editors_to_publishers")
