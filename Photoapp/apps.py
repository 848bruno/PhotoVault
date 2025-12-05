from django.apps import AppConfig

class PhotoappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Photoapp'

    def ready(self):
        import Photoapp.signals

