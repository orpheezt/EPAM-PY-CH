# MLIR Linalg Dialect & Lowering Pipelines RAG Gateway
> **EPAM Challenge 3: "Python Run, Debug the Future — IA con Criterio"**

A high-precision, production-grade Retrieval-Augmented Generation (RAG) system built to answer complex technical queries about the **MLIR Linalg Dialect & Lowering Pipelines (Bufferization / Tensor-to-MemRef)** with zero hallucinations, mandatory source citations, automated evaluation, Hugging Face Inference API integration, and containerized FastAPI service architecture.

---

## 1. Overview & Architecture

The system ingests technical documentation on MLIR lowering transformations, stores vector embeddings in a persistent local or cloud **Qdrant** collection, and exposes a modular FastAPI Gateway (`gateway-py`) with a `POST /ask/` endpoint.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          MLIR KNOWLEDGE BASE                            │
│  data/01_overview.md, data/02_bufferization.md, data/03_one_shot.md ... │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              PEP 723 INGESTION SCRIPT (scripts/ingest.py)               │
│  - DirectoryLoader + TextLoader                                         │
│  - RecursiveCharacterTextSplitter (chunk=600, overlap=80)               │
│  - FastEmbed Embeddings                                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                 VECTOR STORAGE (qdrant_db/mlir_linalg_docs)             │
│  - Local / Cloud Persistent Storage (Cosine Distance, threshold=0.60)   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              FASTAPI GATEWAY SERVER (src/gateway_py/app.py)             │
│  - Modular Module Registry (health, ask)                                │
│  - Hugging Face Inference API (meta-llama/Llama-3.2-3B-Instruct)        │
│  - Strict Grounded System Prompt & Fallback Handler                     │
└─────────────────────────────────────────────────────────────────────────┘
                 │                                        │
                 ▼                                        ▼
┌───────────────────────────────────┐      ┌──────────────────────────────┐
│       POST /ask/ ENDPOINT         │      │     PEP 723 EVAL SCRIPT      │
│ - Accepts JSON AskRequest payload │      │     (scripts/eval.py)        │
│ - Returns AskResponse & Sources   │      │ - Uses httpx2 client         │
│ - OpenAPI Docs at /docs           │      │ - Rich terminal summary      │
└───────────────────────────────────┘      └──────────────────────────────┘
```

---

## 2. Technical Choices

- **Modular Gateway Architecture (`src/gateway_py/`)**: Scalable `Module` registry design (`health`, `ask`) mimicking enterprise gateway patterns.
- **FastAPI & Uvicorn**: High-performance async web engine with auto-generated OpenAPI docs (`/docs`).
- **Hugging Face Inference API**: Powered by `huggingface_hub.InferenceClient` (configurable model: `meta-llama/Llama-3.2-3B-Instruct`).
- **Qdrant Vector Database**: High-performance vector search with local persistent or cloud storage.
- **PEP 723 Standalone Scripts (`scripts/`)**: Ingestion (`scripts/ingest.py`), evaluation (`scripts/eval.py`), and container management (`scripts/image.py`) with inline dependency declarations powered by `rich` and `typer`.
- **`uv` & `uv_build` Backend**: Python `>=3.14` modern build system.
- **Docker Containerization**: Multi-stage Alpine container build tagged as `gateway-py:latest`.

---

## 3. Dataset & Scope

The knowledge base is contained within `./data/` and comprises 8 structured Markdown documents covering:
1. `01_mlir_linalg_overview.md` — Fundamentals of Linalg Dialect & Named Ops.
2. `02_bufferization_concepts.md` — Bufferization concepts (Tensors vs MemRefs).
3. `03_one_shot_bufferize.md` — One-Shot Bufferize pass and allocation strategies.
4. `04_linalg_to_loops_lowering.md` — Lowering Linalg to SCF loops and affine loops.
5. `05_vectorization_passes.md` — Vectorizing Linalg operations.
6. `06_memref_lowering_pipeline.md` — MemRef lowering pipeline details.
7. `07_execution_engine_runner.md` — ExecutionEngine execution & JIT compilation.
8. `08_out_of_scope_topics.md` — Out-of-scope definitions used for fallback testing.

---

## 4. Getting Started

### Prerequisites
- Python `>=3.14`
- [`uv`](https://github.com/astral-sh/uv) installed

### Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/mlir-linalg-rag.git
   cd mlir-linalg-rag
   ```

2. **Sync Virtual Environment**:
   ```bash
   uv sync
   ```

3. **Configure Environment Variables** (Optional for HF LLM generation):
   Create a `.env` file in the root directory:
   ```ini
   HF_TOKEN=your_huggingface_token_here
   HF_MODEL=meta-llama/Llama-3.2-3B-Instruct
   ```

4. **Run Data Ingestion Script**:
   ```bash
   uv run --script scripts/ingest.py
   ```

5. **Launch FastAPI Gateway**:
   ```bash
   uv run uvicorn gateway_py.app:app --host 0.0.0.0 --port 8000
   ```

6. **Query the `POST /ask/` Endpoint**:
   ```bash
   curl -X POST http://localhost:8000/ask/ \
     -H "Content-Type: application/json" \
     -d '{"question": "What is One-Shot Bufferize in MLIR?"}'
   ```

---

## 5. Automated Evaluation Script

Run the automated evaluation suite using the standalone PEP 723 evaluation script (queries gateway via `httpx2`):

```bash
uv run --script scripts/eval.py
```

Evaluation output and benchmark summaries are output to the terminal with `rich` tables and stored in `evaluation_results.json`.

---

## 6. Containerization & OCI Build

Build and containerize the application as `gateway-py`:

```bash
uv run --script scripts/image.py
```

Or build directly with Docker:
```bash
docker build -t gateway-py:latest .
docker run -p 8000:8000 -e HF_TOKEN=$HF_TOKEN gateway-py:latest
```

---

## 7. Deploying to Render

### Option A: Automatic Blueprint Deployment (`render.yaml`)

1. Push your code to GitHub / GitLab.
2. In [Render Dashboard](https://dashboard.render.com), click **New +** -> **Blueprint**.
3. Select your repository. Render will automatically detect [`render.yaml`](file:///home/orpheezt/epam_challenge/ch3/render.yaml).
4. Set your Environment Variables in Render Dashboard:
   - `HF_TOKEN`: Your Hugging Face API token.
   - `QDRANT_URL`: Your Qdrant Cloud URL.
   - `QDRANT_API_KEY`: Your Qdrant API Key.

### Option B: Manual Web Service Deployment

1. Click **New +** -> **Web Service**.
2. Select **Docker** environment.
3. Health Check Path: `/healthz`
4. Set Port to `8000` (or leave default `$PORT`).
5. Add Environment Variables (`HF_TOKEN`, `QDRANT_URL`, `QDRANT_API_KEY`, `HF_MODEL`).

---

### License
MIT License. Developed for EPAM "Python Run, Debug the Future — Challenge 3: IA con Criterio".
