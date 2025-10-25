from django.apps import AppConfig
from .functions.tweet import Tweet
import os


class NewsApplicationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'news_application'

    def ready(self):
        # Ensure signals are imported and registered only once:
        from . import signals
        
    # Without checking this condition, the Tweet instance would be created 
    # twice when using the Django development server due to the auto-reloader.
    # This should have been included in the course material.
        if os.environ.get('RUN_MAIN') == 'true':
            # Skip Twitter initialization in Docker environment
            if not os.environ.get('DOCKER_ENVIRONMENT'):
                Tweet()  # Initialize the Tweet singleton instance
