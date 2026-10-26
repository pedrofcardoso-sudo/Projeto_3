from django.urls import path

from . import views

urlpatterns = [
    path("tarefas/", views.TarefaListCreateView.as_view(), name="tarefa-lista"),
    path("tarefas/<int:pk>/", views.TarefaDetailView.as_view(), name="tarefa-detalhe"),
]
