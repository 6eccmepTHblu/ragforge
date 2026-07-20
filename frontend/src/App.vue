<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { api } from "./api";
import type { CollectionInfo, GraphNode, GraphResponse, Health, QueryResponse } from "./types";
import TopBar from "./components/TopBar.vue";
import AskPanel from "./components/AskPanel.vue";
import IngestPanel from "./components/IngestPanel.vue";
import KnowledgeGraph from "./components/KnowledgeGraph.vue";

const health = ref<Health | null>(null);
const collections = ref<CollectionInfo[]>([]);
const collection = ref("default");
const graph = ref<GraphResponse | null>(null);
const answer = ref<QueryResponse | null>(null);
const highlightIds = ref<string[]>([]);
const selectedNode = ref<GraphNode | null>(null);
const loadingAsk = ref(false);
const busyIngest = ref(false);
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
    graph.value = await api.graph(collection.value);
  } catch (e) {
    graph.value = { collection: collection.value, nodes: [], edges: [] };
    throw e;
  }
}

async function refreshAll() {
  error.value = "";
  try {
    await Promise.all([loadHealth(), loadCollections()]);
    await loadGraph();
  } catch (e) {
    error.value = String(e);
  }
}

async function onAsk(question: string) {
  loadingAsk.value = true;
  error.value = "";
  try {
    const res = await api.query({ question, collection: collection.value });
    answer.value = res;
    highlightIds.value = res.sources.map((s) => s.id);
  } catch (e) {
    error.value = String(e);
  } finally {
    loadingAsk.value = false;
  }
}

async function onIngest(text: string, source: string) {
  busyIngest.value = true;
  error.value = "";
  try {
    await api.ingestText({ text, collection: collection.value, source });
    await loadCollections();
    await loadGraph();
  } catch (e) {
    error.value = String(e);
  } finally {
    busyIngest.value = false;
  }
}

function onCollectionChange(value: string) {
  collection.value = value;
  answer.value = null;
  highlightIds.value = [];
  selectedNode.value = null;
  loadGraph().catch((e) => (error.value = String(e)));
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
    />

    <div class="layout">
      <aside class="sidebar">
        <AskPanel :answer="answer" :loading="loadingAsk" @ask="onAsk" />
        <IngestPanel :busy="busyIngest" @ingest="onIngest" />
      </aside>

      <main class="graph-main">
        <KnowledgeGraph
          :graph="graph"
          :highlight-ids="highlightIds"
          @select="(n) => (selectedNode = n)"
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
        </aside>
      </transition>
    </div>

    <div v-if="error" class="error-toast" @click="error = ''">{{ error }}</div>
  </div>
</template>
