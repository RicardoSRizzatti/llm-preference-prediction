import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Em desenvolvimento (make front-dev), o Vite roda na 5173 e repassa /api para o FastAPI na 8000.
// Em produção (Docker), o FastAPI serve o build (dist/) e a API na mesma porta.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": "http://localhost:8000" },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
    chunkSizeWarningLimit: 1500,
  },
});
