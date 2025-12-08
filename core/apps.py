from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        import core.signals  # noqa
        # Ensure signals are imported when the app is ready
        # This is necessary to connect the signal handlers defined in core/signals.py
        # to the respective model events.
        # The `noqa` comment is used to ignore linting errors for unused imports,