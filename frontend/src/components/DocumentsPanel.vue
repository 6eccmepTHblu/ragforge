<script setup lang="ts">
import type { DocumentInfo } from "../types";

defineProps<{ documents: DocumentInfo[]; busySource: string | null }>();
const emit = defineEmits<{ (e: "delete", source: string): void }>();
</script>

<template>
  <section class="panel">
    <h2>Documents</h2>
    <p v-if="!documents.length" class="muted small">This collection is empty.</p>
    <ul v-else class="doc-list">
      <li v-for="d in documents" :key="d.source" class="doc">
        <div class="doc-body">
          <div class="doc-name">{{ d.source }}</div>
          <div class="doc-meta">{{ d.chunks }} chunk{{ d.chunks === 1 ? "" : "s" }}</div>
        </div>
        <button
          class="btn-danger"
          :disabled="busySource === d.source"
          title="Delete this document"
          @click="emit('delete', d.source)"
        >
          {{ busySource === d.source ? "…" : "✕" }}
        </button>
      </li>
    </ul>
  </section>
</template>
