from django.urls import path

from . import views

app_name = "planillas"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("procesar/<int:anio>/<int:mes>/", views.procesar, name="procesar"),
    path("preplanilla/<int:anio>/<int:mes>/", views.preplanilla, name="preplanilla"),
    path("planilla/<int:anio>/<int:mes>/", views.detalle, name="detalle"),
    path("planilla/<int:anio>/<int:mes>/exportar/<str:formato>/", views.exportar_planilla, name="exportar"),
    path("boleta/<int:nro>/", views.boleta, name="boleta"),
    path("boleta/<int:nro>/exportar/<str:formato>/", views.exportar_boleta, name="exportar_boleta"),
    path("anticipos/", views.anticipos, name="anticipos"),
    path("f110/", views.f110, name="f110"),
]
