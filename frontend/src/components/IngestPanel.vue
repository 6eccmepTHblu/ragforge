<script setup lang="ts">
import { ref } from "vue";

defineProps<{ busy: boolean }>();
const emit = defineEmits<{
  (e: "ingest", text: string, source: string): void;
  (e: "ingest-file", file: File): void;
}>();

const mode = ref<"text" | "file">("text");
const text = ref("");
const source = ref("");
const selectedFile = ref<File | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);

function submitText() {
  const value = text.value.trim();
  if (!value) return;
  emit("ingest", value, source.value.trim() || "pasted.txt");
  text.value = "";
}

function onFileChange(event: Event) {
  const files = (event.target as HTMLInputElement).files;
  selectedFile.value = files && files.length ? files[0] : null;
}

function submitFile() {
  if (!selectedFile.value) return;
  emit("ingest-file", selectedFile.value);
  selectedFile.value = null;
  if (fileInput.value) fileInput.value.value = "";
}
</script>

<template>
  <section class="panel">
    <div class="panel-head">
      <h2>Add knowledge</h2>
      <div class="segmented small-seg">
        <button :class="{ active: mode === 'text' }" @click="mode = 'text'">Text</button>
        <button :class="{ active: mode === 'file' }" @click="mode = 'file'">File</button>
      </div>
    </div>

    <template v-if="mode === 'text'">
      <input v-model="source" class="input" placeholder="Source name (e.g. notes.md)" />
      <textarea
        v-model="text"
        class="input textarea"
        rows="5"
        placeholder="Paste text to chunk, embed and index…"
      ></textarea>
      <button class="btn full" :disabled="busy" @click="submitText">
        {{ busy ? "Indexing…" : "Ingest text" }}
      </button>
    </template>

    <template v-else>
      <label class="filedrop">
        <input
          ref="fileInput"
          type="file"
          accept=".txt,.md,.markdown,.rst,.pdf"
          @change="onFileChange"
        />
        <span class="filedrop-label">
          {{ selectedFile ? selectedFile.name : "Choose a .txt, .md or .pdf file…" }}
        </span>
      </label>
      <p class="muted small">PDF ingestion requires the optional <code>pypdf</code> extra on the server.</p>
      <button class="btn full" :disabled="busy || !selectedFile" @click="submitFile">
        {{ busy ? "Uploading…" : "Upload &amp; index" }}
      </button>
    </template>
  </section>
</template>
