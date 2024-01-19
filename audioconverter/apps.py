from django.apps import AppConfig

class AudioconverterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audioconverter'

    def ready(self):
        import audioconverter.signals
