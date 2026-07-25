<div align="center">

# Advanced RAG Cookbooks

**Practical retrieval and knowledge-assistance projects for building grounded AI experiences.**

[![Python](https://img.shields.io/badge/Python-projects-3776AB?logo=python&logoColor=white)](#project-catalog)
[![Jupyter](https://img.shields.io/badge/Jupyter-notebooks-F37626?logo=jupyter&logoColor=white)](book-recommender-vector-similarity)

[Projects](#project-catalog) · [Quick starts](#quick-starts) · [Screenshot](#real-project-screenshot) · [Limitations](#status-and-limitations)

</div>

## What is it?

This repository is a collection of independent retrieval and knowledge-assistance experiments, not one installable package. Each directory has its own dependencies, runtime assumptions, and data path.

The projects cover a notebook-driven book recommender, a local Llama 3 assistant backed by PostgreSQL/pgvector, and a FastAPI + Chroma document-chat service with a Streamlit UI.

## Project catalog

| Project | Interface | Retrieval / model path | Evidence in the repository |
| --- | --- | --- | --- |
| [`book-recommender-vector-similarity/`](book-recommender-vector-similarity) | Jupyter notebooks | Tagged descriptions and vector similarity over the included book data | Two notebooks, dataset files, and a captured Python environment |
| [`rag-llama3-ollama-webapp/`](rag-llama3-ollama-webapp) | Streamlit | Ollama Llama 3 + Ollama embeddings + PostgreSQL/pgvector | App, assistant configuration, and setup notes |
| [`rag-streamlit-fastapi/`](rag-streamlit-fastapi) | FastAPI and Streamlit | Local Hugging Face embeddings + Chroma + Groq chat model | API, client, sample PDF, persisted Chroma data, API PDF, and screenshots |

## Real project screenshot

The image below is the checked-in Streamlit client for `rag-streamlit-fastapi` after processing a document and starting a chat.

![RAG Streamlit client showing an uploaded PDF and grounded chat response](rag-streamlit-fastapi/imgs/pic.png)

## Quick starts

### Book recommender

```bash
cd book-recommender-vector-similarity
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
jupyter lab
```

Open `data-explore.ipynb` first, then `vector-search.ipynb`. The requirements file is a broad captured environment rather than a minimal dependency set.

### Local Llama 3 + pgvector

Prerequisites: Python, Docker, and Ollama with the `llama3` model available.

```bash
cd rag-llama3-ollama-webapp
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
ollama pull llama3
```

Start the database expected by `assistant.py`:

```bash
docker run -d \
  --name pgvector \
  -e POSTGRES_DB=ai \
  -e POSTGRES_USER=ai \
  -e POSTGRES_PASSWORD=ai \
  -p 5532:5432 \
  phidata/pgvector:16
```

Then run:

```bash
streamlit run app.py
```

### FastAPI + Chroma document chat

```bash
cd rag-streamlit-fastapi
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Create `.env` with a Groq key:

```env
GROQ_API_KEY=your_key_here
```

Run the API and UI in separate terminals:

```bash
python main.py
```

```bash
streamlit run streamlit.py
```

The API documentation is served at `http://localhost:8000/docs`. The Dockerfile runs the API only; the Streamlit client is a separate process.

## Status and limitations

- The projects are independent experiments with no root dependency lock or shared runner.
- `rag-streamlit-fastapi` accepts server-local file paths, keeps chat sessions in memory, enables wildcard CORS, and includes a persisted Chroma database; review these choices before using untrusted data or exposing it publicly.
- Its Streamlit client deletes the temporary upload immediately after the API call and loses chat state on reload.
- The local Ollama project uses the older `phi` package API and a hard-coded PostgreSQL URL.
- The book recommender environment is large and not guaranteed to reproduce across platforms.
- No repository-wide license, CI configuration, or automated test suite is present.
