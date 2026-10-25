from django.urls import path

from . import views

app_name = "cps"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("afiliacion/<int:nro>/", views.detalle, name="detalle"),
    path("afiliacion/<int:nro>/aviso/", views.aviso, name="aviso"),
    path("afiliacion/<int:nro>/afiliar/", views.afiliar, name="afiliar"),
    path("afiliacion/<int:nro>/baja/", views.baja, name="baja"),
    path("afiliacion/<int:nro>/corregir/", views.corregir, name="corregir"),
    path("empleado/<str:ci>/historial/", views.historial, name="historial"),
]
