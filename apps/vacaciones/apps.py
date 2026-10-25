from django.apps import AppConfig


class VacacionesConfig(AppConfig):
    name = "apps.vacaciones"
    label = "vacaciones"
    verbose_name = "Vacaciones y lactancias"

    def ready(self):
        from . import receivers  # noqa: F401
