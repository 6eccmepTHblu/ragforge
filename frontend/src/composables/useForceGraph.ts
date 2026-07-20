/**
 * A small force-directed graph engine on a 2D canvas — no external library.
 *
 * Physics per tick: pairwise repulsion (O(n^2), fine for <= a few hundred
 * nodes), spring attraction along edges, gravity toward the centre, and
 * velocity damping. Supports pan, zoom, node dragging, hover and selection.
 */
import type { GraphNode, GraphResponse } from "../types";

interface SimNode extends GraphNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
  fixed: boolean;
  radius: number;
  color: string;
}

interface SimEdge {
  a: number;
  b: number;
  weight: number;
}

export interface ForceGraphOptions {
  onSelect?: (node: GraphNode | null) => void;
  onHover?: (node: GraphNode | null) => void;
}

export function colorForGroup(group: string): string {
  let hash = 0;
  for (let i = 0; i < group.length; i++) {
    hash = (hash * 31 + group.charCodeAt(i)) & 0xffffffff;
  }
  const hue = Math.abs(hash) % 360;
  return `hsl(${hue}, 70%, 60%)`;
}

export function useForceGraph(canvas: HTMLCanvasElement, options: ForceGraphOptions = {}) {
  const ctx = canvas.getContext("2d")!;
  let nodes: SimNode[] = [];
  let edges: SimEdge[] = [];
  let highlighted = new Set<string>();
  let selectedId: string | null = null;

  let width = 0;
  let height = 0;
  let dpr = Math.max(1, window.devicePixelRatio || 1);

  // View transform: screenCss = offset + world * scale
  let scale = 1;
  let offsetX = 0;
  let offsetY = 0;

  let hoverIndex = -1;
  let dragIndex = -1;
  let panning = false;
  let moved = false;
  let lastX = 0;
  let lastY = 0;
  let raf = 0;

  // Keep the canvas backing store in sync with its CSS size. Called every
  // frame so it self-heals on any layout change (window resize, side panels
  // opening/closing) without relying on ResizeObserver timing.
  function ensureSize() {
    const rect = canvas.getBoundingClientRect();
    dpr = Math.max(1, window.devicePixelRatio || 1);
    const targetW = Math.round(rect.width * dpr);
    const targetH = Math.round(rect.height * dpr);
    width = rect.width;
    height = rect.height;
    if (canvas.width !== targetW || canvas.height !== targetH) {
      canvas.width = targetW;
      canvas.height = targetH;
    }
  }

  function setData(graph: GraphResponse) {
    ensureSize(); // make sure width/height reflect real layout before placing nodes
    const index = new Map<string, number>();
    nodes = graph.nodes.map((n, i) => {
      index.set(n.id, i);
      const angle = (i / Math.max(graph.nodes.length, 1)) * Math.PI * 2;
      const r = 120 + Math.random() * 60;
      return {
        ...n,
        x: width / 2 + Math.cos(angle) * r,
        y: height / 2 + Math.sin(angle) * r,
        vx: 0,
        vy: 0,
        fixed: false,
        radius: Math.min(18, 6 + n.degree * 1.6),
        color: colorForGroup(n.group),
      };
    });
    edges = [];
    for (const e of graph.edges) {
      const a = index.get(e.source);
      const b = index.get(e.target);
      if (a !== undefined && b !== undefined) edges.push({ a, b, weight: e.weight });
    }
    // Reset view roughly centred.
    scale = 1;
    offsetX = 0;
    offsetY = 0;
    selectedId = null;
  }

  function setHighlight(ids: string[]) {
    highlighted = new Set(ids);
  }

  // --- physics -----------------------------------------------------------
  function tick() {
    const repulsion = 2600;
    const springLen = 70;
    const springK = 0.02;
    const gravity = 0.015;
    const damping = 0.86;
    const cx = width / 2;
    const cy = height / 2;

    for (let i = 0; i < nodes.length; i++) {
      const a = nodes[i];
      for (let j = i + 1; j < nodes.length; j++) {
        const b = nodes[j];
        let dx = a.x - b.x;
        let dy = a.y - b.y;
        let d2 = dx * dx + dy * dy;
        if (d2 < 0.01) {
          dx = Math.random() - 0.5;
          dy = Math.random() - 0.5;
          d2 = 0.01;
        }
        const dist = Math.sqrt(d2);
        const force = repulsion / d2;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        a.vx += fx;
        a.vy += fy;
        b.vx -= fx;
        b.vy -= fy;
      }
    }

    for (const e of edges) {
      const a = nodes[e.a];
      const b = nodes[e.b];
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 0.01;
      const rest = springLen / (0.4 + e.weight);
      const force = (dist - rest) * springK;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      a.vx += fx;
      a.vy += fy;
      b.vx -= fx;
      b.vy -= fy;
    }

    for (const n of nodes) {
      n.vx += (cx - n.x) * gravity;
      n.vy += (cy - n.y) * gravity;
      if (n.fixed) {
        n.vx = 0;
        n.vy = 0;
        continue;
      }
      n.vx *= damping;
      n.vy *= damping;
      n.x += n.vx;
      n.y += n.vy;
    }
  }

  // --- rendering ---------------------------------------------------------
  function draw() {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.scale(dpr, dpr);
    ctx.translate(offsetX, offsetY);
    ctx.scale(scale, scale);

    const anyHighlight = highlighted.size > 0;

    for (const e of edges) {
      const a = nodes[e.a];
      const b = nodes[e.b];
      const hot = highlighted.has(a.id) && highlighted.has(b.id);
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.strokeStyle = hot
        ? "rgba(96, 165, 250, 0.9)"
        : `rgba(148, 163, 184, ${0.08 + e.weight * 0.35})`;
      ctx.lineWidth = hot ? 2 : 0.6 + e.weight;
      ctx.stroke();
    }

    for (let i = 0; i < nodes.length; i++) {
      const n = nodes[i];
      const isHi = highlighted.has(n.id);
      const isSel = n.id === selectedId;
      const isHover = i === hoverIndex;
      const dim = anyHighlight && !isHi;

      if (isHi) {
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius + 6, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(96, 165, 250, 0.22)";
        ctx.fill();
      }

      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
      ctx.fillStyle = n.color;
      ctx.globalAlpha = dim ? 0.25 : 1;
      ctx.fill();
      ctx.globalAlpha = 1;

      if (isSel || isHover || isHi) {
        ctx.lineWidth = isSel ? 3 : 2;
        ctx.strokeStyle = isSel ? "#f8fafc" : "#93c5fd";
        ctx.stroke();
      }

      if (isHi || isSel || isHover) {
        ctx.font = "11px ui-sans-serif, system-ui, sans-serif";
        ctx.fillStyle = "rgba(226, 232, 240, 0.95)";
        ctx.fillText(n.label, n.x + n.radius + 4, n.y + 3);
      }
    }
  }

  function frame() {
    ensureSize();
    tick();
    draw();
    raf = requestAnimationFrame(frame);
  }

  // --- interaction -------------------------------------------------------
  function toWorld(clientX: number, clientY: number) {
    const rect = canvas.getBoundingClientRect();
    const cssX = clientX - rect.left;
    const cssY = clientY - rect.top;
    return { x: (cssX - offsetX) / scale, y: (cssY - offsetY) / scale, cssX, cssY };
  }

  function nodeAt(worldX: number, worldY: number): number {
    for (let i = nodes.length - 1; i >= 0; i--) {
      const n = nodes[i];
      const dx = n.x - worldX;
      const dy = n.y - worldY;
      if (dx * dx + dy * dy <= (n.radius + 3) * (n.radius + 3)) return i;
    }
    return -1;
  }

  function onMouseDown(ev: MouseEvent) {
    const { x, y, cssX, cssY } = toWorld(ev.clientX, ev.clientY);
    moved = false;
    lastX = cssX;
    lastY = cssY;
    const hit = nodeAt(x, y);
    if (hit >= 0) {
      dragIndex = hit;
      nodes[hit].fixed = true;
    } else {
      panning = true;
    }
  }

  function onMouseMove(ev: MouseEvent) {
    const { x, y, cssX, cssY } = toWorld(ev.clientX, ev.clientY);
    if (dragIndex >= 0) {
      moved = true;
      nodes[dragIndex].x = x;
      nodes[dragIndex].y = y;
      return;
    }
    if (panning) {
      moved = true;
      offsetX += cssX - lastX;
      offsetY += cssY - lastY;
      lastX = cssX;
      lastY = cssY;
      return;
    }
    const hit = nodeAt(x, y);
    if (hit !== hoverIndex) {
      hoverIndex = hit;
      canvas.style.cursor = hit >= 0 ? "pointer" : "grab";
      options.onHover?.(hit >= 0 ? nodes[hit] : null);
    }
  }

  function onMouseUp(ev: MouseEvent) {
    if (dragIndex >= 0) {
      nodes[dragIndex].fixed = false;
      if (!moved) {
        const n = nodes[dragIndex];
        selectedId = n.id;
        options.onSelect?.(n);
      }
      dragIndex = -1;
    } else if (panning && !moved) {
      const { x, y } = toWorld(ev.clientX, ev.clientY);
      if (nodeAt(x, y) === -1) {
        selectedId = null;
        options.onSelect?.(null);
      }
    }
    panning = false;
  }

  function onWheel(ev: WheelEvent) {
    ev.preventDefault();
    const { cssX, cssY } = toWorld(ev.clientX, ev.clientY);
    const factor = ev.deltaY < 0 ? 1.1 : 1 / 1.1;
    const newScale = Math.min(4, Math.max(0.2, scale * factor));
    // Zoom around the cursor: keep the world point under the cursor fixed.
    offsetX = cssX - ((cssX - offsetX) / scale) * newScale;
    offsetY = cssY - ((cssY - offsetY) / scale) * newScale;
    scale = newScale;
  }

  function resetView() {
    scale = 1;
    offsetX = 0;
    offsetY = 0;
  }

  canvas.addEventListener("mousedown", onMouseDown);
  window.addEventListener("mousemove", onMouseMove);
  window.addEventListener("mouseup", onMouseUp);
  canvas.addEventListener("wheel", onWheel, { passive: false });

  ensureSize();
  frame();

  function destroy() {
    cancelAnimationFrame(raf);
    canvas.removeEventListener("mousedown", onMouseDown);
    window.removeEventListener("mousemove", onMouseMove);
    window.removeEventListener("mouseup", onMouseUp);
    canvas.removeEventListener("wheel", onWheel);
  }

  return { setData, setHighlight, resetView, destroy };
}
