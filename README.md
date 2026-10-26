# API de Tarefas — Projeto 3

API REST de tarefas pessoais feita com Django REST Framework. A autenticação é
por token e cada usuário só consegue consultar e alterar as próprias tarefas.

## Requisitos

- Python 3.10 ou superior
- Banco Supabase/PostgreSQL configurado no `.env`, ou SQLite para desenvolvimento local

## Como executar

No PowerShell, na pasta do projeto:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edite o `.env` com as credenciais do banco. Para o Supabase, preencha
`SUPABASE_DB_NAME`, `SUPABASE_DB_USER`, `SUPABASE_DB_PASSWORD`,
`SUPABASE_DB_HOST` e `SUPABASE_DB_PORT`. Se todos estiverem vazios, o projeto
usa SQLite localmente.

Depois, verifique a configuração, crie as tabelas, cadastre o administrador e
inicie o servidor:

```powershell
python manage.py check
python manage.py makemigrations tarefas
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

O servidor abre por padrão em <http://127.0.0.1:8002/>. O administrador fica
em <http://127.0.0.1:8002/admin/>. A página inicial apresenta os principais links e
instruções para começar a usar a API. A página inicial, a interface navegável
da API e o painel admin permitem escolher entre seis temas (Claro, Noturno,
Oceano, Floresta, Ameixa e Pôr do sol); a escolha fica salva no navegador.
Nas telas da API e do admin, o botão “Início” retorna à página principal.

## Endpoints

| Método | Caminho | Ação |
| --- | --- | --- |
| `POST` | `/api/login/` | Recebe `username` e `password`; retorna um token |
| `GET` | `/api/tarefas/` | Lista as tarefas do usuário autenticado |
| `POST` | `/api/tarefas/` | Cria tarefa; o dono é definido pelo token |
| `GET` | `/api/tarefas/<id>/` | Consulta tarefa própria |
| `PUT` / `PATCH` | `/api/tarefas/<id>/` | Atualiza tarefa própria |
| `DELETE` | `/api/tarefas/<id>/` | Exclui tarefa própria |

A listagem aceita `?concluida=true|false` e
`?prioridade=baixa|media|alta`. Requisições protegidas devem enviar
`Authorization: Token <token>`. Sem token, a API responde `401`; uma tarefa
pertencente a outro usuário responde `404`.

### Exemplos

Login:

```http
POST /api/login/
Content-Type: application/json

{"username": "seu_usuario", "password": "sua_senha"}
```

Criar uma tarefa:

```http
POST /api/tarefas/
Authorization: Token <token>
Content-Type: application/json

{"titulo": "Estudar DRF", "prioridade": "ALTA"}
```

Filtrar tarefas pendentes:

```http
GET /api/tarefas/?concluida=false
Authorization: Token <token>
```

## Testes

Os testes usam um banco SQLite temporário e não gravam no Supabase:

```powershell
python manage.py test --settings=todoapi.test_settings
```

Os testes verificam login, autenticação, filtros válidos e inválidos,
atualização parcial, proteção do dono e isolamento entre usuários. Em produção,
configure uma `SECRET_KEY` própria, defina `DEBUG=False` e configure
`ALLOWED_HOSTS`. O arquivo `.env`, o banco local e o ambiente virtual estão
excluídos do Git; nunca publique senhas, tokens ou chaves secretas.

## Demonstração local com 15 usuários

Os comandos abaixo usam `demo.sqlite3`, um banco separado do Supabase e do
SQLite padrão:

```powershell
python manage.py migrate --settings=todoapi.demo_settings
$env:DEMO_USER_PASSWORD = "defina-uma-senha-local-forte"
$env:DEMO_ADMIN_PASSWORD = "defina-outra-senha-local-forte"
python manage.py seed_demo --settings=todoapi.demo_settings
Remove-Item Env:DEMO_USER_PASSWORD
Remove-Item Env:DEMO_ADMIN_PASSWORD
python manage.py runserver --settings=todoapi.demo_settings
```

O comando de demonstração cria 15 grupos, 15 usuários comuns, 15 tarefas e
obtém 15 tokens pelo endpoint real de login. As contas vão de
`demo_usuario_01` a `demo_usuario_15`. As senhas devem ser definidas por
variáveis de ambiente locais e nunca são incluídas no código. O administrador
local também pode ser configurado com `DEMO_ADMIN_USERNAME` e
`DEMO_ADMIN_EMAIL`. Use essas contas somente na demonstração local. A execução
pode ser repetida sem duplicar grupos ou tarefas. Não use esse comando no
Supabase: ele recusa qualquer banco que não seja o `demo.sqlite3`. A
demonstração testa login, dono definido pelo token, listagem isolada, acesso
cruzado (404), GET/PUT/PATCH/DELETE, validação de filtros e acesso sem token
(401).
