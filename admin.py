from django.contrib import admin

from .models import Tarefa


@admin.register(Tarefa)
class TarefaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "usuario", "prioridade", "concluida", "data_limite")
    list_filter = ("concluida", "prioridade")
    search_fields = ("titulo",)
