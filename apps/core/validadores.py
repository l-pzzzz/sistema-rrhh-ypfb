"""Política de contraseñas (RF-23, regla 1): al menos 8 caracteres, 1 mayúscula y 1 número."""

from django.core.exceptions import ValidationError


class MayusculaYNumeroValidator:
    def validate(self, password, user=None):
        if not any(c.isupper() for c in password) or not any(c.isdigit() for c in password):
            raise ValidationError(
                "La contraseña debe tener al menos una mayúscula y un número.",
                code="clave_debil",
            )

    def get_help_text(self):
        return "La contraseña debe tener al menos una mayúscula y un número."
