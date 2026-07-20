// Mirrors the RAGForge backend API schemas.

export interface Health {
  status: string;
  version: string;
  llm_provider: string;
  embedding_provider: string;
  vectorstore: string;
}

export interface SourceChunk {
  id: string;
  text: string;
  score: number;
  metadata: Record<string, string>;
}

export interface QueryResponse {
  question: string;
  answer: string;
  collection: string;
  sources: SourceChunk[];
  latency_ms: number;
}

export interface SearchResponse {
  query: string;
  collection: string;
  results: SourceChunk[];
}

export interface IngestResponse {
  collection: string;
  documents: number;
  chunks: number;
}

export interface CollectionInfo {
  name: string;
  chunks: number;
}

export interface CollectionsResponse {
  collections: CollectionInfo[];
}

export interface GraphNode {
  id: string;
  label: string;
  group: string;
  text: string;
  degree: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  weight: number;
}

export interface GraphResponse {
  collection: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
}
