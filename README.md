# PharmaShelf

*Know what to stock before the shelf is empty.*

PharmaShelf is a stock and sales assistant for independent pharmacies in Bangladesh. A customer can ask whether a medicine is available at a branch. An owner can review sales, find batches nearing expiry, import Excel records, and ask questions about pharmacy operations with answers grounded in the PharmaShelf Almanac.

For example, if a lot has 17 units left at a unit cost of ৳3.50, the expiry report shows **৳59.50 at risk**. The owner can use that figure alongside the expiry date and sales pace to decide which lot to review first.



## What you can try

| Workflow | Example |
|---|---|
| Customer availability | Ask whether paracetamol is available at `DEMO-01`, then ask about another branch in the same conversation. |
| Counter | Record an incoming batch or a sale. Retrying an identical sale ID records it once and deducts stock once. |
| Owner reports | Review expiry risk, best sellers, and medicine demand over a selected period. |
| Workbook imports | Download a template, map custom Excel headings, preview row errors, and confirm an import. |
| Almanac | Search source-noted entries or ask owner chat a question. A supported answer includes citations. An unrelated question returns an empty source list. |
| MCP | Use a compatible client to search medicines and check branch availability over Streamable HTTP or stdio. |

The assistant is intended for stock and business operations. Questions about diagnosis, treatment, or dosage belong with a pharmacist or doctor.


## Local demo accounts

Run `docker compose up -d --build` and open [the branch workspace](http://localhost:8010/studio/).
The local startup script creates these accounts automatically.

| Account | Email | Password | First thing to try |
|---|---|---|---|
| Owner (`admin`) | `owner@pharmashelf.example.com` | `Demo-Owner-7Qm4-2026!` | Open Reports and request the 30-day expiry report for `DEMO-01`. |
| Pharmacist (`staff`) | `staff@pharmashelf.example.com` | `Demo-Staff-9Kp2-2026!` | Sign in through Swagger and check your role at `GET /api/v1/auth/me`. |
| Customer (`customer`) | `customer@pharmashelf.example.com` | `Demo-Customer-3Vr8-2026!` | Sign in through Swagger to try the customer account. |

For a quick public demo, open **Availability** and ask “Is paracetamol available at DEMO-01?” No login is required.

These shared credentials are for the local Docker demo. Hosted accounts are managed separately.

## Run locally with Docker

You need Git, Docker with Compose, a Gemini API key for generated answers, and internet access on the first start to download the container images and embedding model. The supplied CPU embedding image targets Intel/AMD x86-64. The commands below use PowerShell.

### 1. Clone and configure

Clone the repository using the Git link above. From the repository root, run:

```powershell
Copy-Item .env.example .env
notepad .env
```

Set the following values in your local `.env`. Keep the real file out of Git.

| Setting | Purpose |
|---|---|
| `APP_NAME`, `DEBUG` | Application name and debug mode. Use `DEBUG=false` for the demo. |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Local PostgreSQL database and credentials. Choose a private database password. |
| `DB_HOST`, `DB_PORT` | Compose sets the API connection to `db:5432`. |
| `JWT_SECRET`, `ACCESS_TOKEN_MINUTES` | Token signing secret and token lifetime. Generate a fresh secret for each deployment. |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | API key and a Gemini model available to that key. |
| `PHARMASHELF_HOST_PORT` | Local API port. The default is `8010`. |

To generate a JWT secret locally with Python:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 2. Start the stack

```powershell
docker compose up -d --build
docker compose logs -f api
```

Compose starts the FastAPI backend, PostgreSQL 17 with pgvector, and a CPU embedding service. On the first boot, allow several minutes for the model download. The API startup script applies Alembic migrations, seeds the demo inventory and Almanac, waits for a valid embedding, ingests the Almanac passages, and starts Uvicorn.

When Uvicorn reports that startup is complete, press `Ctrl+C` to leave the log view. The containers continue running.

| Local entry point | URL |
|---|---|
| Branch workspace | [localhost:8010/studio/](http://localhost:8010/studio/) |
| Swagger API explorer | [localhost:8010/docs](http://localhost:8010/docs) |
| Health | [localhost:8010/api/v1/health](http://localhost:8010/api/v1/health) |
| MCP for Streamable HTTP clients | `http://localhost:8010/mcp` |

If you changed `PHARMASHELF_HOST_PORT`, use that port in these URLs.

### 3. Check the seed data

```powershell
$api = 'http://localhost:8010/api/v1'
Invoke-RestMethod "$api/health"
Invoke-RestMethod "$api/medicines/DEMO-PARA-500"
Invoke-RestMethod "$api/inventory/availability?sku=DEMO-PARA-500&branch_code=DEMO-01"
```

A fresh-clone check with separate, empty Docker volumes verified that the API became healthy, `DEMO-PARA-500` was present, and four Almanac entries were indexed with 384-dimensional embeddings.

To stop the stack while keeping local data:

```powershell
docker compose stop
```
<!-- 
## API examples

### Read a medicine record

The medicine catalog uses a SKU for single-record lookup. This is the read operation in the catalog CRUD API. Swagger shows the routes, request schemas, and authorization requirements for the other operations.

```powershell
$api = 'http://localhost:8010/api/v1'
$medicine = Invoke-RestMethod "$api/medicines/DEMO-PARA-500"
$medicine | Select-Object sku, name, generic_name, strength, dosage_form
```

### Ask customer chat about stock

```powershell
$question = 'Is paracetamol available at DEMO-01?'
$body = @{ content = $question } | ConvertTo-Json

$first = Invoke-RestMethod -Method Post -Uri "$api/chat" `
    -ContentType 'application/json' -Body $body -TimeoutSec 75

$first | ConvertTo-Json -Depth 5
```

For a follow-up, send the conversation history:

```powershell
$body = @{
    history = @(
        @{ role = 'user'; content = $question }
        @{ role = 'assistant'; content = $first.reply }
    )
    content = 'And at NO-SUCH-BRANCH?'
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Method Post -Uri "$api/chat" `
    -ContentType 'application/json' -Body $body -TimeoutSec 75
``` -->

### Sign in and request an owner report

Use an account with the `admin` role in the database being tested. Credentials from one deployment do not automatically create an account in another.

```powershell
$owner = Get-Credential -Message 'Enter your PharmaShelf owner email and password'
$login = Invoke-RestMethod -Method Post -Uri "$api/auth/login" -Body @{
    username = $owner.UserName
    password = $owner.GetNetworkCredential().Password
}
$headers = @{ Authorization = "Bearer $($login.access_token)" }

Invoke-RestMethod `
    -Uri "$api/inventory/expiry-rescue?branch_code=DEMO-01&days=30" `
    -Headers $headers | ConvertTo-Json -Depth 6
```

### Ask an owner question with citations

```powershell
$body = @{
    content = 'How should I choose which expiring batch to review first?'
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "$api/chat/owner" `
    -Headers $headers -ContentType 'application/json' `
    -Body $body -TimeoutSec 75 | ConvertTo-Json -Depth 6
```

The verified expiry example returned citation `[1]` and source slug `prioritizing-expiring-lots`. Asking how to tune a violin returned a no-match reply and `sources: []`.

## How the system works

| Flow | Implementation |
|---|---|
| API and database | FastAPI controllers receive requests. Dependencies supply services and database sessions. Repositories query PostgreSQL through async SQLAlchemy. Pydantic schemas define API inputs and outputs. |
| Customer chat and tools | Gemini selects `search_medicines` or `check_availability`. The backend runs the tool against the catalog or inventory service and sends the result back to Gemini. |
| Almanac RAG | Ingestion splits entries into overlapping passages and sends them to `BAAI/bge-small-en-v1.5`. PostgreSQL stores each 384-dimensional vector with its passage. Owner chat embeds the question, retrieves active passages using cosine distance, and supplies matching evidence to Gemini. The API resolves citation numbers to database source notes. |
| MCP | One server exposes two database-backed tools, a live availability resource, and a lookup prompt. The same server supports Streamable HTTP and stdio. |
| Authorization | Owner endpoints require bearer authentication and the admin role. Public customer availability exposes a stock availability flag. |

### Useful files

| Path | Purpose |
|---|---|
| `app/main.py` | FastAPI application, exception handlers, frontend mount, and MCP HTTP lifespan |
| `app/modules/` | Feature modules for auth, medicines, inventory, sales, imports, chat, and Almanac |
| `app/integrations/llm/gemini.py` | Gemini integration for tool calls and grounded answers |
| `app/modules/almanac/retrieval.py` | Semantic passage retrieval |
| `app/mcp_server.py` | MCP tools, resource, prompt, and stdio entry point |
| `scripts/start_local.py` | Local migration, seed, embedding readiness, ingestion, and API startup |
| `scripts/ingest_almanac.py` | Chunking, embedding, and database ingestion |
| `scripts/start_render.py` | Render startup command implementation |
| `alembic/versions/` | Database migrations |

To refresh the vector index after editing Almanac entries:

```powershell
docker compose exec -T api python -m scripts.ingest_almanac
```

## MCP client setup

For **Streamable HTTP**, configure the client URL as `http://localhost:8010/mcp`.

For **stdio**, start the Compose stack first. From the repository root, configure the client to launch:

```text
docker compose exec -T api python -m app.mcp_server
```

| Capability | Name |
|---|---|
| Tool | `search_medicines` |
| Tool | `check_availability` |
| Resource | `pharmashelf://demo/availability` |
| Prompt | `availability_lookup` |

Both transports were checked locally with the MCP Python client. The HTTP check called both tools, read the resource, and rendered the prompt.

## Business model and demo

The target buyer is an independent pharmacy owner in Bangladesh, especially one supervising multiple branches. The proposed model is a monthly pharmacy subscription, an additional fee for extra branches, and optional one-time setup to import historical Excel data.

A short demo can follow one medicine through the system: check its availability as a customer, preview an Excel sale, open the owner’s expiry report, then ask which lot deserves attention first. Show the calculated BDT amount at risk alongside the Almanac source that explains how to act on it.