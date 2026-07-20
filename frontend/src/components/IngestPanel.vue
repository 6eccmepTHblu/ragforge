<script setup lang="ts">
import { ref } from "vue";

defineProps<{ busy: boolean }>();
const emit = defineEmits<{ (e: "ingest", text: string, source: string): void }>();

const text = ref("");
const source = ref("");

function submit() {
  const value = text.value.trim();
  if (!value) return;
  emit("ingest", value, source.value.trim() || "pasted.txt");
  text.value = "";
}
</script>

<template>
  <section class="panel">
    <h2>Add knowledge</h2>
    <input v-model="source" class="input" placeholder="Source name (e.g. notes.md)" />
    <textarea
      v-model="text"
      class="input textarea"
      rows="5"
      placeholder="Paste text to chunk, embed and index…"
    ></textarea>
    <button class="btn full" :disabled="busy" @click="submit">
      {{ busy ? "Indexing…" : "Ingest" }}
    </button>
  </section>
</template>
