<script setup lang="ts">
import type { CollectionInfo, Health } from "../types";

defineProps<{
  health: Health | null;
  collections: CollectionInfo[];
  collection: string;
}>();
const emit = defineEmits<{
  (e: "update:collection", value: string): void;
  (e: "refresh"): void;
}>();
</script>

<template>
  <header class="topbar">
    <div class="brand">
      <span class="logo">◈</span>
      <div class="brand-text">
        <h1>RAGForge</h1>
        <p>Knowledge Explorer</p>
      </div>
    </div>

    <div class="topbar-right">
      <div class="badges" v-if="health">
        <span class="badge">v{{ health.version }}</span>
        <span class="badge">llm · {{ health.llm_provider }}</span>
        <span class="badge">emb · {{ health.embedding_provider }}</span>
        <span class="badge">store · {{ health.vectorstore }}</span>
      </div>
      <label class="select">
        <span>Collection</span>
        <select
          :value="collection"
          @change="emit('update:collection', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="c in collections" :key="c.name" :value="c.name">
            {{ c.name }} · {{ c.chunks }}
          </option>
        </select>
      </label>
      <button class="btn-ghost" title="Refresh" @click="emit('refresh')">↻</button>
    </div>
  </header>
</template>
