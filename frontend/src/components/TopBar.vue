<script setup lang="ts">
import { nextTick, ref } from "vue";
import type { CollectionInfo, Health } from "../types";

defineProps<{
  health: Health | null;
  collections: CollectionInfo[];
  collection: string;
}>();
const emit = defineEmits<{
  (e: "update:collection", value: string): void;
  (e: "refresh"): void;
  (e: "create-collection", name: string): void;
  (e: "delete-collection"): void;
}>();

const creating = ref(false);
const newName = ref("");
const nameInput = ref<HTMLInputElement | null>(null);

async function startCreate() {
  creating.value = true;
  await nextTick();
  nameInput.value?.focus();
}

function confirmCreate() {
  const name = newName.value.trim();
  if (name) emit("create-collection", name);
  newName.value = "";
  creating.value = false;
}
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

      <div class="collection-controls" v-if="!creating">
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
        <button class="btn-ghost" title="New collection" @click="startCreate">＋</button>
        <button class="btn-danger" title="Delete this collection" @click="emit('delete-collection')">
          🗑
        </button>
      </div>

      <div class="collection-create" v-else>
        <input
          ref="nameInput"
          v-model="newName"
          class="input"
          placeholder="new-collection-name"
          @keyup.enter="confirmCreate"
          @keyup.esc="creating = false"
        />
        <button class="btn" @click="confirmCreate">Create</button>
        <button class="btn-ghost" @click="creating = false">✕</button>
      </div>

      <button class="btn-ghost" title="Refresh" @click="emit('refresh')">↻</button>
    </div>
  </header>
</template>
