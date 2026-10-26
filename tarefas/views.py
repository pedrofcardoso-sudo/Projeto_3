from rest_framework import generics
from rest_framework.exceptions import ValidationError

from .models import Tarefa
from .serializers import TarefaSerializer


class TarefaListCreateView(generics.ListCreateAPIView):
    serializer_class = TarefaSerializer

    def get_queryset(self):
        queryset = Tarefa.objects.filter(usuario=self.request.user)

        concluida = self.request.query_params.get("concluida")
        if concluida is not None:
            concluida = concluida.strip().lower()
            if concluida not in {"true", "false"}:
                raise ValidationError(
                    {"concluida": "Use 'true' ou 'false'."}
                )
            queryset = queryset.filter(concluida=concluida == "true")

        prioridade = self.request.query_params.get("prioridade")
        if prioridade:
            prioridade = prioridade.strip().upper()
            prioridades_validas = {
                valor for valor, _ in Tarefa.PRIORIDADE_CHOICES
            }
            if prioridade not in prioridades_validas:
                raise ValidationError(
                    {"prioridade": "Use 'baixa', 'media' ou 'alta'."}
                )
            queryset = queryset.filter(prioridade=prioridade)

        return queryset

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


class TarefaDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TarefaSerializer

    def get_queryset(self):
        return Tarefa.objects.filter(usuario=self.request.user)
