from django.apps import AppConfig


class ReportesConfig(AppConfig):
    name = "apps.reportes"
    label = "reportes"
    verbose_name = "Reportes"

    def ready(self):
        from . import receivers  # noqa: F401
