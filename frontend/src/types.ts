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

export interface DocumentInfo {
  source: string;
  chunks: number;
}

export interface DocumentsResponse {
  collection: string;
  documents: DocumentInfo[];
}

export interface DeleteResponse {
  collection: string;
  deleted: number;
}

export interface JudgeResponse {
  faithfulness: number;
  answer_relevancy: number;
  reasoning: string;
}

export interface StreamHandlers {
  onSources?: (sources: SourceChunk[]) => void;
  onToken?: (token: string) => void;
  onDone?: () => void;
}

// UI-side representation of an answer that fills in as it streams.
export interface StreamingAnswer {
  question: string;
  text: string;
  sources: SourceChunk[];
  latencyMs: number;
  streaming: boolean;
}
