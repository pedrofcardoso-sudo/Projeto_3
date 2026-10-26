from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from .models import Tarefa

User = get_user_model()


class TarefasAPITest(APITestCase):
    def setUp(self):
        self.ana = User.objects.create_user(username="ana", password="senha123")
        self.beto = User.objects.create_user(username="beto", password="senha123")
        self.tok_ana = Token.objects.create(user=self.ana)
        self.tok_beto = Token.objects.create(user=self.beto)
        self.t1 = Tarefa.objects.create(
            titulo="Estudar Django",
            prioridade="ALTA",
            usuario=self.ana,
        )
        self.t2 = Tarefa.objects.create(
            titulo="Lavar o carro",
            prioridade="BAIXA",
            concluida=True,
            usuario=self.ana,
        )
        self.t3 = Tarefa.objects.create(
            titulo="Tarefa do Beto",
            prioridade="ALTA",
            usuario=self.beto,
        )

    def como(self, token):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        return client

    def test_seletor_de_tema_na_pagina_inicial(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        for theme in (
            "Claro",
            "Noturno",
            "Oceano",
            "Floresta",
            "Ameixa",
            "Pôr do sol",
        ):
            self.assertContains(response, theme)

    def test_seletor_de_tema_na_interface_navegavel_da_api(self):
        response = self.client.get(
            reverse("tarefa-lista"),
            HTTP_ACCEPT="text/html",
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn(b"Tema do site", response.content)
        for theme in (
            "Claro",
            "Noturno",
            "Oceano",
            "Floresta",
            "Ameixa",
            "Pôr do sol",
        ):
            self.assertIn(theme.encode(), response.content)
        self.assertIn(b'class="home-button" href="/"', response.content)

    def test_seletor_de_tema_no_painel_admin(self):
        response = self.client.get("/admin/login/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"/static/tarefas/themes.css", response.content)
        self.assertIn(b"/static/tarefas/themes.js", response.content)

    def test_login_devolve_token(self):
        response = self.client.post(
            reverse("api-login"),
            {"username": "ana", "password": "senha123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["token"], self.tok_ana.key)

    def test_sem_token_retorna_401(self):
        self.assertEqual(self.client.get(reverse("tarefa-lista")).status_code, 401)

    def test_lista_apenas_tarefas_do_proprio_usuario(self):
        response = self.como(self.tok_ana).get(reverse("tarefa-lista"))
        titulos = {tarefa["titulo"] for tarefa in response.data}
        self.assertEqual(titulos, {"Estudar Django", "Lavar o carro"})

    def test_filtros_por_conclusao_e_prioridade(self):
        client = self.como(self.tok_ana)
        response = client.get(reverse("tarefa-lista") + "?prioridade=Alta")
        self.assertEqual([item["titulo"] for item in response.data], ["Estudar Django"])

        response = client.get(reverse("tarefa-lista") + "?concluida=true")
        self.assertEqual([item["titulo"] for item in response.data], ["Lavar o carro"])

        response = client.get(
            reverse("tarefa-lista") + "?concluida=false&prioridade=alta"
        )
        self.assertEqual([item["titulo"] for item in response.data], ["Estudar Django"])

    def test_filtros_invalidos_retorna_400(self):
        client = self.como(self.tok_ana)
        self.assertEqual(
            client.get(reverse("tarefa-lista") + "?concluida=talvez").status_code,
            400,
        )
        self.assertEqual(
            client.get(reverse("tarefa-lista") + "?prioridade=urgente").status_code,
            400,
        )

    def test_criacao_define_dono_pelo_token(self):
        response = self.como(self.tok_ana).post(
            reverse("tarefa-lista"),
            {"titulo": "Nova tarefa", "usuario": self.beto.pk},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            Tarefa.objects.get(titulo="Nova tarefa").usuario,
            self.ana,
        )

    def test_atualizacao_nao_permite_trocar_dono(self):
        response = self.como(self.tok_ana).patch(
            reverse("tarefa-detalhe", args=[self.t1.pk]),
            {"usuario": self.beto.pk, "titulo": "Título atualizado"},
        )
        self.assertEqual(response.status_code, 200)
        self.t1.refresh_from_db()
        self.assertEqual(self.t1.usuario, self.ana)
        self.assertEqual(self.t1.titulo, "Título atualizado")

    def test_patch_atualiza_parcialmente(self):
        response = self.como(self.tok_ana).patch(
            reverse("tarefa-detalhe", args=[self.t1.pk]),
            {"concluida": True},
        )
        self.assertEqual(response.status_code, 200)
        self.t1.refresh_from_db()
        self.assertTrue(self.t1.concluida)
        self.assertEqual(self.t1.titulo, "Estudar Django")
        self.assertEqual(self.t1.prioridade, "ALTA")

    def test_tarefa_de_outro_usuario_retorna_404(self):
        client = self.como(self.tok_beto)
        url = reverse("tarefa-detalhe", args=[self.t1.pk])
        self.assertEqual(client.get(url).status_code, 404)
        self.assertEqual(client.patch(url, {"concluida": True}).status_code, 404)
        self.assertEqual(client.delete(url).status_code, 404)
        self.assertTrue(Tarefa.objects.filter(pk=self.t1.pk).exists())

    def test_delete_da_propria_tarefa(self):
        response = self.como(self.tok_ana).delete(
            reverse("tarefa-detalhe", args=[self.t2.pk])
        )
        self.assertEqual(response.status_code, 204)
