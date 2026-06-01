from django.apps import AppConfig


class MoviesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'movies'
    
    # ---------------------------
    # What This Does"
    # -> ready() is a special Django method that runs automatically when the server starts. Think of it like:
    
    # Server starts → Django loads all apps → 
    # calls ready() on each app → scheduler starts → 
    # cleaner runs every 60 seconds forever
    
    def ready(self):
        import os
        if not os.getenv('VERCEL'):
            from . import scheduler
            scheduler.start()