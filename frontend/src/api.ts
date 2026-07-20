import type {
  CollectionsResponse,
  GraphResponse,
  Health,
  IngestResponse,
  QueryResponse,
  SearchResponse,
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

export const api = {
  health: () => request<Health>("/health"),

  collections: () => request<CollectionsResponse>("/collections"),

  ingestText: (payload: { text: string; collection?: string; source?: string }) =>
    request<IngestResponse>("/ingest/text", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

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

  graph: (collection: string, k = 4, minSim = 0.12) =>
    request<GraphResponse>(
      `/graph?collection=${encodeURIComponent(collection)}&k=${k}&min_sim=${minSim}`,
    ),
};
