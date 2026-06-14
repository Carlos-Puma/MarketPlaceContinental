from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("registro/", views.register_view, name="register"),
    path("mi-cuenta/", views.user_panel_view, name="user_panel"),
    path("mi-cuenta/editar/", views.user_edit_view, name="user_edit"),
    path("vendedor/registro/", views.seller_register_view, name="seller_register"),
]
