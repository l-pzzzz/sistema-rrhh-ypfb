from django.apps import AppConfig


class AdministracionConfig(AppConfig):
    name = "apps.administracion"
    label = "administracion"
    verbose_name = "Administración"

    def ready(self):
        from . import receivers  # noqa: F401
