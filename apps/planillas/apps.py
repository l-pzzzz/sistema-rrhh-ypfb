from django.apps import AppConfig


class PlanillasConfig(AppConfig):
    name = "apps.planillas"
    label = "planillas"
    verbose_name = "Planillas de sueldos"

    def ready(self):
        from . import receivers  # noqa: F401
