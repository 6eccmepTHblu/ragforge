<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { api } from "./api";
import type {
  CollectionInfo,
  DocumentInfo,
  GraphNode,
  GraphResponse,
  Health,
  JudgeResponse,
  SourceChunk,
  StreamingAnswer,
} from "./types";
import TopBar from "./components/TopBar.vue";
import AskPanel from "./components/AskPanel.vue";
import IngestPanel from "./components/IngestPanel.vue";
import DocumentsPanel from "./components/DocumentsPanel.vue";
import KnowledgeGraph from "./components/KnowledgeGraph.vue";

const health = ref<Health | null>(null);
const collections = ref<CollectionInfo[]>([]);
const collection = ref("default");
const graph = ref<GraphResponse | null>(null);
const documents = ref<DocumentInfo[]>([]);
const answer = ref<StreamingAnswer | null>(null);
const judge = ref<JudgeResponse | null>(null);
const searchResults = ref<SourceChunk[] | null>(null);
const highlightIds = ref<string[]>([]);
const selectedNode = ref<GraphNode | null>(null);
const loadingAsk = ref(false);
const searching = ref(false);
const judging = ref(false);
const busyIngest = ref(false);
const busySource = ref<string | null>(null);
const deletingChunk = ref(false);
const graphK = ref(4);
const graphMinSim = ref(0.12);
const error = ref("");

const collectionsForSelect = computed<CollectionInfo[]>(() => {
  const list = [...collections.value];
  if (!list.some((c) => c.name === collection.value)) {
    list.unshift({ name: collection.value, chunks: 0 });
  }
  return list;
});

async function loadHealth() {
  health.value = await api.health();
}
async function loadCollections() {
  const res = await api.collections();
  collections.value = res.collections;
  if (collections.value.length && !collections.value.some((c) => c.name === collection.value)) {
    collection.value = collections.value[0].name;
  }
}
async function loadGraph() {
  try {
    graph.value = await api.graph(collection.value, graphK.value, graphMinSim.value);
  } catch (e) {
    graph.value = { collection: collection.value, nodes: [], edges: [] };
    throw e;
  }
}
async function loadDocuments() {
  documents.value = (await api.documents(collection.value)).documents;
}

async function refreshAll() {
  error.value = "";
  try {
    await Promise.all([loadHealth(), loadCollections()]);
    await Promise.all([loadGraph(), loadDocuments()]);
  } catch (e) {
    error.value = String(e);
  }
}

function resetResults() {
  answer.value = null;
  judge.value = null;
  searchResults.value = null;
  highlightIds.value = [];
}

async function onAsk(question: string) {
  loadingAsk.value = true;
  judge.value = null;
  searchResults.value = null;
  error.value = "";
  const started = performance.now();
  answer.value = { question, text: "", sources: [], latencyMs: 0, streaming: true };
  try {
    await api.queryStream(
      { question, collection: collection.value },
      {
        onSources: (sources) => {
          if (answer.value) answer.value.sources = sources;
          highlightIds.value = sources.map((s) => s.id);
        },
        onToken: (token) => {
          if (answer.value) answer.value.text += token;
        },
      },
    );
    if (answer.value) answer.value.latencyMs = Math.round(performance.now() - started);
  } catch (e) {
    error.value = String(e);
  } finally {
    loadingAsk.value = false;
    if (answer.value) answer.value.streaming = false;
  }
}

async function onSearch(query: string) {
  searching.value = true;
  answer.value = null;
  judge.value = null;
  error.value = "";
  try {
    const res = await api.search({ query, collection: collection.value });
    searchResults.value = res.results;
    highlightIds.value = res.results.map((r) => r.id);
  } catch (e) {
    error.value = String(e);
  } finally {
    searching.value = false;
  }
}

async function onJudge() {
  if (!answer.value) return;
  judging.value = true;
  error.value = "";
  try {
    judge.value = await api.judge({
      question: answer.value.question,
      answer: answer.value.text,
      contexts: answer.value.sources.map((s) => s.text),
    });
  } catch (e) {
    error.value = String(e);
  } finally {
    judging.value = false;
  }
}

async function onIngest(text: string, source: string) {
  busyIngest.value = true;
  error.value = "";
  try {
    await api.ingestText({ text, collection: collection.value, source });
    await Promise.all([loadCollections(), loadGraph(), loadDocuments()]);
  } catch (e) {
    error.value = String(e);
  } finally {
    busyIngest.value = false;
  }
}

async function onIngestFile(file: File) {
  busyIngest.value = true;
  error.value = "";
  try {
    await api.ingestFile(file, collection.value);
    await Promise.all([loadCollections(), loadGraph(), loadDocuments()]);
  } catch (e) {
    error.value = String(e);
  } finally {
    busyIngest.value = false;
  }
}

async function onDeleteDocument(source: string) {
  busySource.value = source;
  error.value = "";
  try {
    await api.deleteDocument(source, collection.value);
    if (selectedNode.value?.group === source) selectedNode.value = null;
    await Promise.all([loadCollections(), loadGraph(), loadDocuments()]);
  } catch (e) {
    error.value = String(e);
  } finally {
    busySource.value = null;
  }
}

async function onDeleteChunk(id: string) {
  deletingChunk.value = true;
  error.value = "";
  try {
    await api.deleteChunk(id, collection.value);
    selectedNode.value = null;
    highlightIds.value = highlightIds.value.filter((x) => x !== id);
    await Promise.all([loadCollections(), loadGraph(), loadDocuments()]);
  } catch (e) {
    error.value = String(e);
  } finally {
    deletingChunk.value = false;
  }
}

function onCollectionChange(value: string) {
  collection.value = value;
  resetResults();
  selectedNode.value = null;
  Promise.all([loadGraph(), loadDocuments()]).catch((e) => (error.value = String(e)));
}

function onCreateCollection(name: string) {
  if (collections.value.some((c) => c.name === name)) {
    onCollectionChange(name);
    return;
  }
  collection.value = name;
  resetResults();
  selectedNode.value = null;
  Promise.all([loadGraph(), loadDocuments()]).catch((e) => (error.value = String(e)));
}

async function onDeleteCollection() {
  if (!confirm(`Delete collection "${collection.value}" and all of its chunks?`)) return;
  error.value = "";
  try {
    await api.deleteCollection(collection.value);
    resetResults();
    selectedNode.value = null;
    await loadCollections();
    if (!collections.value.some((c) => c.name === collection.value)) {
      collection.value = collections.value[0]?.name ?? "default";
    }
    await Promise.all([loadGraph(), loadDocuments()]);
  } catch (e) {
    error.value = String(e);
  }
}

let graphParamsTimer: number | undefined;
function onGraphParams(k: number, minSim: number) {
  graphK.value = k;
  graphMinSim.value = minSim;
  clearTimeout(graphParamsTimer);
  graphParamsTimer = window.setTimeout(
    () => loadGraph().catch((e) => (error.value = String(e))),
    150,
  );
}

onMounted(refreshAll);
</script>

<template>
  <div class="app">
    <TopBar
      :health="health"
      :collections="collectionsForSelect"
      :collection="collection"
      @update:collection="onCollectionChange"
      @refresh="refreshAll"
      @create-collection="onCreateCollection"
      @delete-collection="onDeleteCollection"
    />

    <div class="layout">
      <aside class="sidebar">
        <AskPanel
          :answer="answer"
          :loading="loadingAsk"
          :judge="judge"
          :judging="judging"
          :search-results="searchResults"
          :searching="searching"
          @ask="onAsk"
          @search="onSearch"
          @judge="onJudge"
        />
        <IngestPanel :busy="busyIngest" @ingest="onIngest" @ingest-file="onIngestFile" />
        <DocumentsPanel
          :documents="documents"
          :busy-source="busySource"
          @delete="onDeleteDocument"
        />
      </aside>

      <main class="graph-main">
        <KnowledgeGraph
          :graph="graph"
          :highlight-ids="highlightIds"
          :k="graphK"
          :min-sim="graphMinSim"
          @select="(n) => (selectedNode = n)"
          @params="onGraphParams"
        />
      </main>

      <transition name="slide">
        <aside class="details" v-if="selectedNode">
          <div class="details-head">
            <h2>Chunk</h2>
            <button class="btn-ghost" @click="selectedNode = null">✕</button>
          </div>
          <span class="chip">{{ selectedNode.group }}</span>
          <span class="chip ghost">degree {{ selectedNode.degree }}</span>
          <p class="detail-text">{{ selectedNode.text }}</p>
          <button
            class="btn-danger full"
            :disabled="deletingChunk"
            @click="onDeleteChunk(selectedNode.id)"
          >
            {{ deletingChunk ? "Deleting…" : "Delete this chunk" }}
          </button>
        </aside>
      </transition>
    </div>

    <div v-if="error" class="error-toast" @click="error = ''">{{ error }}</div>
  </div>
</template>
