"""Configuración del Sistema de Información para la Gestión de RRHH – YPFB-Andina.

Solo la modifica el agente de la fase base o el integrador (AGENTS.md §3).
"""

from pathlib import Path
from urllib.parse import quote

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CSRF_TRUSTED_ORIGINS=(list, []),
)
environ.Env.read_env(BASE_DIR / ".env")

# Sin valores por defecto: las credenciales solo vienen del entorno o de .env (no versionado).
SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.core",
    "apps.kardex",
    "apps.cps",
    "apps.planillas",
    "apps.vacaciones",
    "apps.finiquitos",
    "apps.administracion",
    "apps.reportes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.core.auditoria.AuditoriaMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.menu",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Base de datos: MySQL 8, una sola base bd_rrhh (docs/06).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env("DB_NAME", default="bd_rrhh"),
        "USER": env("DB_USER", default="rrhh"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST", default="127.0.0.1"),
        "PORT": env("DB_PORT", default="3306"),
        "OPTIONS": {"charset": "utf8mb4", "init_command": "SET sql_mode='STRICT_TRANS_TABLES'"},
        "TEST": {"CHARSET": "utf8mb4", "COLLATION": "utf8mb4_0900_ai_ci"},
    }
}

# Redis con contraseña (REDIS_PASSWORD). Sin Redis configurado se usa una caché local en memoria.
REDIS_PASSWORD = env("REDIS_PASSWORD", default="")
REDIS_HOST = env("REDIS_HOST", default="127.0.0.1")


def _url_redis(base):
    clave = f":{quote(REDIS_PASSWORD, safe='')}@" if REDIS_PASSWORD else ""
    return f"redis://{clave}{REDIS_HOST}:6379/{base}"


REDIS_URL = env("REDIS_URL", default=_url_redis(1))
CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": REDIS_URL}
    if REDIS_PASSWORD or env("REDIS_URL", default="")
    else {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
}

# Usuarios y autenticación (CU-16, RF-27, RNF-06 a RNF-08).
AUTH_USER_MODEL = "administracion.Usuario"
AUTHENTICATION_BACKENDS = ["apps.administracion.backends.BackendUsuario"]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "apps.core.validadores.MayusculaYNumeroValidator"},
]
LOGIN_URL = "administracion:login"
LOGIN_REDIRECT_URL = "inicio"
LOGOUT_REDIRECT_URL = "administracion:login"
MAX_INTENTOS_FALLIDOS = 3
MINUTOS_BLOQUEO = 15

SESSION_COOKIE_AGE = 15 * 60
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# HTTPS lo termina nginx (RNF-05).
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = env.bool("COOKIES_SEGURAS", default=not DEBUG)
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE

LANGUAGE_CODE = "es-bo"
TIME_ZONE = "America/La_Paz"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = env("MEDIA_ROOT", default=str(BASE_DIR / "media"))

# Documentos digitalizados (RF-04): PDF, JPG o PNG de hasta 5 MB.
DOCUMENTO_TAMANO_MAXIMO = 5 * 1024 * 1024
DOCUMENTO_EXTENSIONES = ["pdf", "jpg", "jpeg", "png"]

# Celery + Redis (docs/06, tareas programadas).
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default=_url_redis(0))
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)

# Las tareas de cada app (PROGRAMACION en apps/<app>/tasks.py) se unen en config/celery.py.
APPS_CON_TAREAS = ["kardex", "cps"]

# Correo: consola por defecto (desarrollo); en producción EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend.
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="rrhh@localhost")


def _correos(nombre):
    """Lista de direcciones de una variable del .env separadas por comas; vacía = solo pantalla."""
    return [d.strip() for d in env(nombre, default="").split(",") if d.strip()]


# Destinatarios de las alertas: Kardex y CPS (RF-03, RF-07, RF-08), Vacaciones y lactancias (RF-19),
# Planillas y respaldos (RF-14, RF-25).
CORREO_AFILIADORES = _correos("CORREO_AFILIADORES")
CORREO_RESP_VACACIONES = _correos("CORREO_RESP_VACACIONES")
CORREO_ADMINISTRADOR = _correos("CORREO_ADMINISTRADOR")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
