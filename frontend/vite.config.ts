import path from "node:path";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "./src"),
    },
  },
  server: {
    port: 5173,
  },
  preview: {
    // Railway (and most PaaS hosts) put the app behind a generated
    // *.up.railway.app domain -- Vite's preview server rejects unrecognized
    // Host headers by default (a DNS-rebinding guard), which would 403 every
    // request in production unless explicitly allowed here.
    allowedHosts: true,
  },
});
