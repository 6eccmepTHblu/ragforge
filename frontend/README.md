# RAGForge Frontend

A Vue 3 + TypeScript + Vite dashboard for the RAGForge API: ingest documents,
ask questions, and explore the **semantic knowledge graph** of your chunks.

The graph is a from-scratch force-directed engine on `<canvas>` (no graph
library): nodes are chunks, edges are cosine-similarity links, node size scales
with degree, colour encodes the source document. Ask a question and the answer's
source chunks light up in the graph.

The UI covers the full API surface:

- **Ingestion** — paste text or **upload a file** (`.txt` / `.md` / `.pdf`).
- **Answer or Search** — full RAG answer, or raw hybrid retrieval with no
  generation.
- **Streaming answers** over Server-Sent Events with a typing effect; sources
  highlight in the graph as soon as they arrive.
- **In-UI evaluation** — an LLM-as-judge button scores faithfulness and answer
  relevancy as meters.
- **Collection management** — create, switch and delete collections.
- **Deletion** — remove a whole document (Documents panel) or a single chunk
  (select a graph node → Delete).
- **Graph controls** — neighbours (`k`) and min-similarity sliders rebuild the
  `/graph` on the fly.

## Production build (Docker)

`docker compose up --build` from the repo root builds this app, serves it with
nginx and reverse-proxies `/api` to the backend. See `Dockerfile` and
`nginx.conf`.

## Develop

```bash
# 1. Start the backend (from the repo root)
uvicorn app.main:app --reload           # http://localhost:8000

# 2. Start the frontend
cd frontend
npm install
npm run dev                             # http://localhost:5173
```

The API base URL defaults to `http://localhost:8000` and can be overridden:

```bash
VITE_API_BASE=http://localhost:8000 npm run dev
```

## Build

```bash
npm run build      # type-checks with vue-tsc, then bundles to dist/
npm run preview
```

## Stack

- Vue 3 (`<script setup>`, Composition API) + TypeScript (strict)
- Vite 6
- Canvas 2D force-directed graph (custom composable, `src/composables/useForceGraph.ts`)
