import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// The frontend talks to the RAGForge API directly (the backend enables CORS).
// Override the target in dev with VITE_API_BASE if the API runs elsewhere.
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
  },
});
