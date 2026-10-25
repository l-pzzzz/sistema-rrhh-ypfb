from django.apps import AppConfig


class KardexConfig(AppConfig):
    name = "apps.kardex"
    label = "kardex"
    verbose_name = "Kardex y contratos"

    def ready(self):
        from . import receivers  # noqa: F401
