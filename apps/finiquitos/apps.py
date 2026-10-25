from django.apps import AppConfig


class FiniquitosConfig(AppConfig):
    name = "apps.finiquitos"
    label = "finiquitos"
    verbose_name = "Finiquitos y evaluaciones"

    def ready(self):
        from . import receivers  # noqa: F401
