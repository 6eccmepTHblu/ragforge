<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import type { GraphNode, GraphResponse } from "../types";
import { colorForGroup, useForceGraph } from "../composables/useForceGraph";

const props = defineProps<{ graph: GraphResponse | null; highlightIds: string[] }>();
const emit = defineEmits<{ (e: "select", node: GraphNode | null): void }>();

const canvasEl = ref<HTMLCanvasElement | null>(null);
let engine: ReturnType<typeof useForceGraph> | null = null;

const legend = computed(() => {
  const groups = new Set<string>();
  for (const n of props.graph?.nodes ?? []) groups.add(n.group);
  return [...groups].map((g) => ({ group: g, color: colorForGroup(g) }));
});

const isEmpty = computed(() => (props.graph?.nodes.length ?? 0) === 0);

onMounted(() => {
  if (!canvasEl.value) return;
  engine = useForceGraph(canvasEl.value, { onSelect: (n) => emit("select", n) });
  if (props.graph) engine.setData(props.graph);
  engine.setHighlight(props.highlightIds);
});

watch(
  () => props.graph,
  (g) => {
    if (engine && g) engine.setData(g);
  },
);
watch(
  () => props.highlightIds,
  (ids) => engine?.setHighlight(ids),
  { deep: true },
);

onBeforeUnmount(() => engine?.destroy());
</script>

<template>
  <div class="graph-wrap">
    <canvas ref="canvasEl" class="graph-canvas"></canvas>

    <div class="graph-legend" v-if="legend.length">
      <span v-for="l in legend" :key="l.group" class="legend-item">
        <span class="legend-dot" :style="{ background: l.color }"></span>{{ l.group }}
      </span>
    </div>

    <div class="graph-toolbar">
      <button class="btn-ghost" @click="engine?.resetView()">Reset view</button>
      <span class="hint">
        {{ graph?.nodes.length ?? 0 }} chunks · {{ graph?.edges.length ?? 0 }} links ·
        drag nodes, scroll to zoom
      </span>
    </div>

    <div v-if="isEmpty" class="graph-empty">
      <p>No chunks yet.</p>
      <p class="muted">Ingest a document to build the semantic graph.</p>
    </div>
  </div>
</template>
