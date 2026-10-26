from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path(
        "",
        TemplateView.as_view(template_name="tarefas/home.html"),
        name="home",
    ),
    path("admin/", admin.site.urls),
    path("api/login/", obtain_auth_token, name="api-login"),
    path("api/", include("tarefas.urls")),
]
