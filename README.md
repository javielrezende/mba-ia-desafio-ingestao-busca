# Desafio MBA — Engenharia de Software com IA (Full Cycle)

Aplicação de **RAG (Retrieval-Augmented Generation)** sobre PDF: o texto do documento é extraído, dividido em **chunks**, convertido em **embeddings** com a API Google (Gemini) e armazenado no **PostgreSQL com pgvector**. O **chat** consulta o banco por similaridade e responde **somente com base no conteúdo indexado**.

## O que você precisa na máquina

- **Docker** e **Docker Compose** instalados e em execução.

**Não é necessário ter Python instalado no host.** O interpretador e as dependências rodam dentro do container `python_dev` definido no `docker-compose.yml`.

## Como funciona (visão rápida)

1. **`docker compose up`** sobe o Postgres (com extensão `vector`), um job que garante a extensão e o container da aplicação Python. O serviço `python_app` fica ativo com `sleep infinity` para você **executar comandos sob demanda** — manter esses containers em pé é o que mantém o ambiente pronto para ingestão e chat.
2. **`src/ingest.py`** lê o PDF (caminho via variáveis de ambiente), gera os chunks, calcula embeddings e **grava no banco**.
3. **`src/chat.py`** abre um loop interativo: sua pergunta é usada para buscar trechos relevantes no banco e o modelo responde com base nesse contexto.

**Ordem obrigatória:** primeiro a **ingestão**, depois o **chat**. Sem rodar o ingest pelo menos uma vez (com um PDF válido), não há chunks no banco para o chat consultar.

## Configuração

1. Copie o exemplo de variáveis e preencha os valores reais (em especial a chave da API Google):

   ```bash
   cp .env.example .env
   ```

2. Edite o `.env`. Campos esperados (veja também `src/ingest.py` e `src/search.py`):

   | Variável | Uso |
   |----------|-----|
   | `GOOGLE_API_KEY` | Chave da API Google (Gemini). |
   | `GOOGLE_EMBEDDING_MODEL` | Modelo de embeddings (ex.: `models/gemini-embedding-2-preview`). |
   | `DATABASE_URL` | URL SQLAlchemy/psycopg para o Postgres. **Dentro do Compose**, use o hostname do serviço `postgres`, por exemplo: `postgresql+psycopg://postgres:postgres@postgres:5432/rag` |
   | `PG_VECTOR_COLLECTION_NAME` | Nome da coleção lógica no pgvector (ex.: `challenge_collection`). |
   | `PDF_PATH` | Caminho **dentro do container** para o PDF ou para a pasta que o contém. O projeto é montado em `/app`, então um arquivo na raiz do repositório costuma ser `/app/seu-arquivo.pdf`. Se for **diretório**, o nome do arquivo pode ser definido com `PDF_FILENAME` (padrão: `document.pdf`). |

3. Coloque o arquivo **PDF** no repositório (ou ajuste `PDF_PATH` / `PDF_FILENAME`) de acordo com o que você configurou.

## Subir o ambiente

Na raiz do repositório:

```bash
docker compose up -d
```

Isso mantém os serviços rodando em segundo plano. Para ver logs ou status:

```bash
docker compose ps
docker compose logs -f
```

## 1 — Ingestão (obrigatório antes do chat)

Executa o Python **dentro** do container `python_dev`:

```bash
docker compose exec python_app python src/ingest.py
```

(Se o nome do serviço no seu `docker-compose.yml` for outro, use-o no lugar de `python_app`; o container costuma aparecer como `python_dev`.)

O script valida variáveis de ambiente, localiza o PDF, extrai texto, sanitiza UTF-8, faz o split em chunks, gera embeddings e persiste no Postgres/pgvector.

## 2 — Chat

Modo interativo (é necessário `-it` para o `input()` funcionar):

```bash
docker compose exec -it python_app python src/chat.py
```

Digite perguntas sobre o conteúdo do PDF. Para sair: `exit`, `quit` ou `Ctrl+C`.

## Encerrar

```bash
docker compose down
```

Para remover também o volume do Postgres (apaga os dados indexados):

```bash
docker compose down -v
```

## Estrutura relevante

- `src/ingest.py` — ingestão do PDF → chunks → embeddings → banco.
- `src/chat.py` — CLI do chat.
- `src/search.py` — busca por similaridade + prompt + modelo de chat.
- `docker-compose.yml` — Postgres (pgvector), bootstrap da extensão `vector`, container Python.
- `Dockerfile` — imagem Python 3.11 com dependências do `requirements.txt`.
