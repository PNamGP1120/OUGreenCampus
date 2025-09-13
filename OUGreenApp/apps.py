from django.apps import AppConfig


class OugreenappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'OUGreenApp'

    def ready(self):
        import OUGreenApp.signals

