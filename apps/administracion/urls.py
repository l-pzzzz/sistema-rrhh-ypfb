from django.urls import path

from . import views

app_name = "administracion"

urlpatterns = [
    path("login/", views.InicioSesionView.as_view(), name="login"),
    path("logout/", views.CierreSesionView.as_view(), name="logout"),
]
