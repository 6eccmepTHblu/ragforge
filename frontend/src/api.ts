import type {
  CollectionsResponse,
  DeleteResponse,
  DocumentsResponse,
  GraphResponse,
  Health,
  IngestResponse,
  JudgeResponse,
  QueryResponse,
  SearchResponse,
  StreamHandlers,
} from "./types";

const BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "content-type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText} — ${detail}`);
  }
  return (await res.json()) as T;
}

const qs = (params: Record<string, string>) =>
  new URLSearchParams(params).toString();

// Parse a single SSE event block ("event: X\ndata: Y").
function dispatchEvent(raw: string, handlers: StreamHandlers) {
  let event = "message";
  let data = "";
  for (const line of raw.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) data += line.slice(5).trim();
  }
  if (!data) return;
  if (event === "sources") handlers.onSources?.(JSON.parse(data));
  else if (event === "token") handlers.onToken?.(JSON.parse(data));
  else if (event === "done") handlers.onDone?.();
}

export const api = {
  health: () => request<Health>("/health"),

  collections: () => request<CollectionsResponse>("/collections"),

  documents: (collection: string) =>
    request<DocumentsResponse>(`/documents?${qs({ collection })}`),

  ingestText: (payload: { text: string; collection?: string; source?: string }) =>
    request<IngestResponse>("/ingest/text", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Multipart upload — let the browser set the content-type/boundary itself.
  async ingestFile(file: File, collection: string): Promise<IngestResponse> {
    const form = new FormData();
    form.append("file", file);
    form.append("collection", collection);
    const res = await fetch(`${BASE}/ingest/file`, { method: "POST", body: form });
    if (!res.ok) {
      const detail = await res.text().catch(() => "");
      throw new Error(`${res.status} ${res.statusText} — ${detail}`);
    }
    return (await res.json()) as IngestResponse;
  },

  query: (payload: { question: string; collection?: string; top_k?: number }) =>
    request<QueryResponse>("/query", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  search: (payload: { query: string; collection?: string; top_k?: number }) =>
    request<SearchResponse>("/search", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  judge: (payload: { question: string; answer: string; contexts: string[] }) =>
    request<JudgeResponse>("/eval/judge", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  graph: (collection: string, k = 4, minSim = 0.12) =>
    request<GraphResponse>(`/graph?${qs({ collection, k: String(k), min_sim: String(minSim) })}`),

  deleteChunk: (chunkId: string, collection: string) =>
    request<DeleteResponse>(`/chunks/${encodeURIComponent(chunkId)}?${qs({ collection })}`, {
      method: "DELETE",
    }),

  deleteDocument: (source: string, collection: string) =>
    request<DeleteResponse>(`/documents?${qs({ source, collection })}`, {
      method: "DELETE",
    }),

  deleteCollection: (name: string) =>
    request<{ status: string; collection: string }>(
      `/collections/${encodeURIComponent(name)}`,
      { method: "DELETE" },
    ),

  // Stream a RAG answer over Server-Sent Events.
  async queryStream(
    payload: { question: string; collection?: string; top_k?: number },
    handlers: StreamHandlers,
  ): Promise<void> {
    const res = await fetch(`${BASE}/query/stream`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok || !res.body) {
      throw new Error(`${res.status} ${res.statusText}`);
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let idx: number;
      while ((idx = buffer.indexOf("\n\n")) >= 0) {
        dispatchEvent(buffer.slice(0, idx), handlers);
        buffer = buffer.slice(idx + 2);
      }
    }
    if (buffer.trim()) dispatchEvent(buffer, handlers);
  },
};
