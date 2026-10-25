from django.apps import AppConfig


class CpsConfig(AppConfig):
    name = "apps.cps"
    label = "cps"
    verbose_name = "Seguro de salud CPS"

    def ready(self):
        from . import receivers  # noqa: F401
