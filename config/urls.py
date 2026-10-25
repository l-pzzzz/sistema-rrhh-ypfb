from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from apps.core.views import inicio

urlpatterns = [
    path("", inicio, name="inicio"),
    path("", include("apps.administracion.urls")),
    path("kardex/", include("apps.kardex.urls")),
    path("cps/", include("apps.cps.urls")),
    path("planillas/", include("apps.planillas.urls")),
    path("vacaciones/", include("apps.vacaciones.urls")),
    path("finiquitos/", include("apps.finiquitos.urls")),
    path("reportes/", include("apps.reportes.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = "apps.core.views.acceso_denegado"
