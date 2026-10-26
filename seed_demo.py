from pathlib import Path
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import BaseCommand, CommandError
from django.db import transaction
from rest_framework.test import APIClient

from tarefas.models import Tarefa


class Command(BaseCommand):
    help = "Cria e testa dados de demonstração no SQLite local isolado."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=15,
            help="Quantidade de grupos, usuários, tarefas e tokens (padrão: 15).",
        )
        parser.add_argument(
            "--password",
            default=os.getenv("DEMO_USER_PASSWORD"),
            help="Senha das contas de demonstração (ou DEMO_USER_PASSWORD).",
        )
        parser.add_argument(
            "--admin-username",
            default=os.getenv("DEMO_ADMIN_USERNAME", "demo_admin"),
            help="Nome do administrador local (ou DEMO_ADMIN_USERNAME).",
        )
        parser.add_argument(
            "--admin-email",
            default=os.getenv("DEMO_ADMIN_EMAIL", "demo_admin@example.test"),
            help="E-mail do administrador local (ou DEMO_ADMIN_EMAIL).",
        )
        parser.add_argument(
            "--admin-password",
            default=os.getenv("DEMO_ADMIN_PASSWORD"),
            help="Senha do administrador, ou variável DEMO_ADMIN_PASSWORD.",
        )

    def handle(self, *args, **options):
        if options["count"] < 15:
            raise CommandError("--count deve ser pelo menos 15.")
        if not options["password"]:
            raise CommandError(
                "Defina DEMO_USER_PASSWORD ou informe --password para criar "
                "as contas de demonstração."
            )

        connection = transaction.get_connection()
        configured_database = connection.settings_dict["NAME"]
        expected_database = (settings.BASE_DIR / "demo.sqlite3").resolve()
        if (
            connection.vendor != "sqlite"
            or Path(configured_database).resolve() != expected_database
        ):
            raise CommandError(
                "Este comando só pode gravar em demo.sqlite3. Use "
                "--settings=todoapi.demo_settings para evitar alterar o Supabase."
            )

        count = options["count"]
        password = options["password"]
        User = get_user_model()

        with transaction.atomic():
            groups = [
                Group.objects.get_or_create(name=f"demo_grupo_{index:02d}")[0]
                for index in range(1, count + 1)
            ]
            users = []
            for index, group in enumerate(groups, start=1):
                username = f"demo_usuario_{index:02d}"
                user, _ = User.objects.get_or_create(
                    username=username,
                    defaults={
                        "email": f"{username}@example.test",
                        "is_active": True,
                    },
                )
                user.email = f"{username}@example.test"
                user.is_active = True
                user.set_password(password)
                user.save()
                user.groups.add(group)
                if not user.groups.filter(pk=group.pk).exists():
                    raise CommandError(f"Grupo não associado a {username}.")
                users.append(user)

            admin_user, admin_created = User.objects.get_or_create(
                username=options["admin_username"],
                defaults={"email": options["admin_email"]},
            )
            if admin_created and not options["admin_password"]:
                raise CommandError(
                    "Informe --admin-password ou defina DEMO_ADMIN_PASSWORD "
                    "para criar o administrador local."
                )
            admin_user.email = options["admin_email"]
            admin_user.is_active = True
            admin_user.is_staff = True
            admin_user.is_superuser = True
            if options["admin_password"]:
                admin_user.set_password(options["admin_password"])
            admin_user.save()
            User.objects.filter(is_superuser=True).exclude(pk=admin_user.pk).update(
                is_superuser=False,
                is_staff=False,
            )

        tokens = []
        task_ids = []
        priorities = ("BAIXA", "MEDIA", "ALTA")
        client = APIClient()

        for index, user in enumerate(users):
            login_response = client.post(
                "/api/login/",
                {"username": user.username, "password": password},
                format="json",
                HTTP_HOST="localhost",
            )
            if login_response.status_code != 200:
                raise CommandError(
                    f"Login falhou para {user.username}: "
                    f"HTTP {login_response.status_code}."
                )

            token = login_response.data.get("token")
            if not token:
                raise CommandError(f"Login de {user.username} não retornou token.")
            tokens.append(token)

            client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
            other_user_id = users[(index + 1) % count].pk
            title = f"Tarefa de demonstração {index + 1:02d}"
            task = Tarefa.objects.filter(usuario=user, titulo=title).first()
            if task is None:
                create_response = client.post(
                    "/api/tarefas/",
                    {
                        "titulo": title,
                        "descricao": f"Tarefa local do usuário {user.username}.",
                        "prioridade": priorities[index % len(priorities)],
                        "concluida": index % 2 == 0,
                        "usuario": other_user_id,
                    },
                    format="json",
                    HTTP_HOST="localhost",
                )
                if create_response.status_code != 201:
                    raise CommandError(
                        f"Criação da tarefa de {user.username} falhou: "
                        f"HTTP {create_response.status_code}."
                    )
                if create_response.data.get("usuario") != user.pk:
                    raise CommandError(
                        f"A API não preservou o dono correto para {user.username}."
                    )
                task_id = create_response.data["id"]
            else:
                task_id = task.pk
            task_ids.append(task_id)

        for index, (user, token, task_id) in enumerate(
            zip(users, tokens, task_ids, strict=True)
        ):
            client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
            response = client.get("/api/tarefas/", HTTP_HOST="localhost")
            if response.status_code != 200:
                raise CommandError(
                    f"Listagem falhou para {user.username}: "
                    f"HTTP {response.status_code}."
                )
            if not any(item["id"] == task_id for item in response.data):
                raise CommandError(
                    f"Isolamento de listagem falhou para {user.username}."
                )
            if any(
                item["id"] in task_ids and item["id"] != task_id
                for item in response.data
            ):
                raise CommandError(
                    f"A listagem de {user.username} contém tarefa de outro usuário."
                )

            foreign_task_id = task_ids[(index + 1) % count]
            response = client.get(
                f"/api/tarefas/{foreign_task_id}/",
                HTTP_HOST="localhost",
            )
            if response.status_code != 404:
                raise CommandError(
                    f"Isolamento de detalhe falhou para {user.username}: "
                    f"HTTP {response.status_code}."
                )

            response = client.get(
                f"/api/tarefas/{task_id}/",
                HTTP_HOST="localhost",
            )
            if response.status_code != 200:
                raise CommandError(
                    f"Consulta da tarefa própria de {user.username} falhou."
                )

            response = client.put(
                f"/api/tarefas/{task_id}/",
                {
                    "titulo": f"Tarefa de demonstração {index + 1:02d}",
                    "descricao": f"Tarefa local do usuário {user.username}.",
                    "concluida": False,
                    "prioridade": priorities[index % len(priorities)],
                    "data_limite": None,
                    "usuario": other_user_id,
                },
                format="json",
                HTTP_HOST="localhost",
            )
            if (
                response.status_code != 200
                or response.data["usuario"] != user.pk
                or response.data["concluida"]
            ):
                raise CommandError(
                    f"PUT ou proteção do dono falhou para {user.username}."
                )

            response = client.patch(
                f"/api/tarefas/{task_id}/",
                {"concluida": True},
                format="json",
                HTTP_HOST="localhost",
            )
            if response.status_code != 200 or not response.data["concluida"]:
                raise CommandError(
                    f"PATCH da tarefa de {user.username} falhou."
                )

            response = client.get(
                "/api/tarefas/?prioridade=invalida",
                HTTP_HOST="localhost",
            )
            if response.status_code != 400:
                raise CommandError(
                    f"Validação de filtro falhou para {user.username}: "
                    f"HTTP {response.status_code}."
                )

            temporary_response = client.post(
                "/api/tarefas/",
                {
                    "titulo": f"Excluir após teste {index + 1:02d}",
                    "prioridade": "BAIXA",
                },
                format="json",
                HTTP_HOST="localhost",
            )
            if temporary_response.status_code != 201:
                raise CommandError(
                    f"Criação para teste de DELETE falhou para {user.username}."
                )
            response = client.delete(
                f"/api/tarefas/{temporary_response.data['id']}/",
                HTTP_HOST="localhost",
            )
            if response.status_code != 204:
                raise CommandError(
                    f"DELETE da própria tarefa falhou para {user.username}."
                )

        client.credentials()
        response = client.get("/api/tarefas/", HTTP_HOST="localhost")
        if response.status_code != 401:
            raise CommandError(
                f"A API sem token deveria responder 401, recebeu "
                f"{response.status_code}."
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"OK: {Group.objects.filter(name__startswith='demo_grupo_').count()} "
                f"grupos, {User.objects.filter(username__startswith='demo_usuario_').count()} "
                f"usuários comuns, "
                f"{Tarefa.objects.filter(titulo__startswith='Tarefa de demonstração ').count()} "
                f"tarefas e {len(tokens)} tokens confirmados no SQLite local."
            )
        )
        self.stdout.write(
            "Contas: demo_usuario_01 até "
            f"demo_usuario_{count:02d} | senha definida via ambiente/argumento."
        )
        self.stdout.write(
            f"Único administrador local: {admin_user.username} "
            f"({admin_user.email}); senha definida via ambiente/argumento."
        )
        self.stdout.write(
            "Testados: login real/token, grupos, CRUD, dono protegido, listagem "
            "isolada, 404 entre usuários, filtros e 401 sem token."
        )
