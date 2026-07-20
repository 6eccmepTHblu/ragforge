<script setup lang="ts">
import { ref } from "vue";
import type { QueryResponse } from "../types";

defineProps<{ answer: QueryResponse | null; loading: boolean }>();
const emit = defineEmits<{ (e: "ask", question: string): void }>();

const question = ref("");

function submit() {
  const q = question.value.trim();
  if (q) emit("ask", q);
}
</script>

<template>
  <section class="panel">
    <h2>Ask</h2>
    <div class="ask-row">
      <input
        v-model="question"
        class="input"
        placeholder="Ask a question about your documents…"
        @keyup.enter="submit"
      />
      <button class="btn" :disabled="loading" @click="submit">
        {{ loading ? "…" : "Ask" }}
      </button>
    </div>

    <div v-if="answer" class="answer">
      <p class="answer-text">{{ answer.answer }}</p>
      <div class="answer-meta">
        {{ answer.latency_ms }} ms · {{ answer.sources.length }} sources · highlighted in graph →
      </div>
      <ul class="sources">
        <li v-for="(s, i) in answer.sources" :key="s.id" class="source">
          <span class="source-rank">[{{ i + 1 }}]</span>
          <div class="source-body">
            <div class="source-head">
              {{ s.metadata.source ?? "unknown" }} · {{ s.score.toFixed(3) }}
            </div>
            <div class="source-text">{{ s.text.slice(0, 160) }}…</div>
          </div>
        </li>
      </ul>
    </div>
    <p v-else class="muted small">
      Ask a question — the answer's source chunks light up in the graph.
    </p>
  </section>
</template>
