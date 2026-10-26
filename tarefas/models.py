from django.conf import settings
from django.db import models


class Tarefa(models.Model):
    PRIORIDADE_CHOICES = [
        ("BAIXA", "Baixa"),
        ("MEDIA", "Média"),
        ("ALTA", "Alta"),
    ]

    titulo = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    concluida = models.BooleanField(default=False)
    prioridade = models.CharField(
        max_length=5,
        choices=PRIORIDADE_CHOICES,
        default="MEDIA",
    )
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_limite = models.DateField(null=True, blank=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tarefas",
    )

    class Meta:
        ordering = ["-data_criacao", "-id"]

    def __str__(self):
        return self.titulo
