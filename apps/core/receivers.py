"""Invalida la caché del Singleton de parámetros al guardar un PARAMETRO."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .parametros import parametros


@receiver(post_save, sender="administracion.Parametro")
def invalidar_parametros(sender, instance, **kwargs):
    parametros.invalidar(instance.gestion_id)
