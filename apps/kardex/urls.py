from django.urls import path

from . import views

app_name = "kardex"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("empleados/nuevo/", views.empleado_nuevo, name="empleado_nuevo"),
    path("empleados/<str:ci>/", views.ficha, name="ficha"),
    path("empleados/<str:ci>/editar/", views.empleado_editar, name="empleado_editar"),
    path("empleados/<str:ci>/contratos/nuevo/", views.contrato_nuevo, name="contrato_nuevo"),
    path("empleados/<str:ci>/dependientes/nuevo/", views.dependiente_nuevo, name="dependiente_nuevo"),
    path("personas/<str:ci>/documentos/nuevo/", views.documento_adjuntar, name="documento_adjuntar"),
    path("documentos/<int:nro>/", views.documento_ver, name="documento_ver"),
    path("documentos/<int:nro>/reemplazar/", views.documento_reemplazar, name="documento_reemplazar"),
    path("contratos/<int:nro>/editar/", views.contrato_editar, name="contrato_editar"),
    path("contratos/<int:nro>/retiro/", views.contrato_retiro, name="contrato_retiro"),
    path("dependientes/<str:ci>/editar/", views.dependiente_editar, name="dependiente_editar"),
]
