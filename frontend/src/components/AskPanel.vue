<script setup lang="ts">
import { ref } from "vue";
import type { JudgeResponse, SourceChunk, StreamingAnswer } from "../types";

defineProps<{
  answer: StreamingAnswer | null;
  loading: boolean;
  judge: JudgeResponse | null;
  judging: boolean;
  searchResults: SourceChunk[] | null;
  searching: boolean;
}>();
const emit = defineEmits<{
  (e: "ask", question: string): void;
  (e: "search", query: string): void;
  (e: "judge"): void;
}>();

const mode = ref<"answer" | "search">("answer");
const input = ref("");

function submit() {
  const value = input.value.trim();
  if (!value) return;
  if (mode.value === "answer") emit("ask", value);
  else emit("search", value);
}

function pct(v: number) {
  return `${Math.round(v * 100)}%`;
}
</script>

<template>
  <section class="panel">
    <div class="panel-head">
      <h2>{{ mode === "answer" ? "Ask" : "Search" }}</h2>
      <div class="segmented small-seg">
        <button :class="{ active: mode === 'answer' }" @click="mode = 'answer'">Answer</button>
        <button :class="{ active: mode === 'search' }" @click="mode = 'search'">Search</button>
      </div>
    </div>

    <div class="ask-row">
      <input
        v-model="input"
        class="input"
        :placeholder="
          mode === 'answer'
            ? 'Ask a question about your documents…'
            : 'Semantic + keyword search…'
        "
        @keyup.enter="submit"
      />
      <button class="btn" :disabled="loading || searching" @click="submit">
        {{ loading || searching ? "…" : mode === "answer" ? "Ask" : "Search" }}
      </button>
    </div>

    <!-- Answer (RAG) mode -->
    <div v-if="mode === 'answer' && answer" class="answer">
      <p class="answer-text">
        {{ answer.text }}<span v-if="answer.streaming" class="cursor">▋</span>
      </p>
      <div class="answer-meta" v-if="!answer.streaming">
        {{ answer.latencyMs }} ms · {{ answer.sources.length }} sources · highlighted in graph →
      </div>

      <ul class="sources" v-if="answer.sources.length">
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

      <div class="judge-row" v-if="!answer.streaming && answer.text">
        <button class="btn-ghost" :disabled="judging" @click="emit('judge')">
          {{ judging ? "Judging…" : "Evaluate answer (LLM-as-judge)" }}
        </button>
      </div>

      <div v-if="judge" class="judge">
        <div class="metric">
          <div class="metric-label">
            <span>Faithfulness</span><span>{{ pct(judge.faithfulness) }}</span>
          </div>
          <div class="meter"><div class="meter-fill" :style="{ width: pct(judge.faithfulness) }"></div></div>
        </div>
        <div class="metric">
          <div class="metric-label">
            <span>Answer relevancy</span><span>{{ pct(judge.answer_relevancy) }}</span>
          </div>
          <div class="meter"><div class="meter-fill alt" :style="{ width: pct(judge.answer_relevancy) }"></div></div>
        </div>
        <p class="judge-reason">{{ judge.reasoning }}</p>
      </div>
    </div>

    <!-- Search (retrieval only) mode -->
    <div v-else-if="mode === 'search' && searchResults" class="answer">
      <div class="answer-meta">
        {{ searchResults.length }} results · retrieval only, no generation · highlighted in graph →
      </div>
      <ul class="sources" v-if="searchResults.length">
        <li v-for="(s, i) in searchResults" :key="s.id" class="source">
          <span class="source-rank">{{ i + 1 }}</span>
          <div class="source-body">
            <div class="source-head">
              {{ s.metadata.source ?? "unknown" }} · {{ s.score.toFixed(4) }}
            </div>
            <div class="source-text">{{ s.text.slice(0, 160) }}…</div>
          </div>
        </li>
      </ul>
      <p v-else class="muted small">No matches.</p>
    </div>

    <p v-else class="muted small">
      {{
        mode === "answer"
          ? "Ask a question — the answer streams in and its source chunks light up in the graph."
          : "Run a hybrid (dense + BM25) search and see the ranked chunks."
      }}
    </p>
  </section>
</template>
