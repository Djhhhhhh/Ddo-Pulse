import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

type ViteEnv = {
  vitePort: number;
  proxyTarget: string;
  apiBase: string;
  appTitle: string;
};

const defaults: ViteEnv = {
  vitePort: 5173,
  proxyTarget: "http://127.0.0.1:8765",
  apiBase: "/api",
  appTitle: "Ddo-Pulse",
};

function loadViteEnv(): ViteEnv {
  const envPath = path.join(__dirname, ".ddo-pulse.env.json");
  if (!fs.existsSync(envPath)) {
    return defaults;
  }
  try {
    const raw = JSON.parse(fs.readFileSync(envPath, "utf-8")) as Partial<ViteEnv>;
    return { ...defaults, ...raw };
  } catch {
    return defaults;
  }
}

const env = loadViteEnv();

export default defineConfig({
  plugins: [vue()],
  server: {
    port: env.vitePort,
    proxy: {
      [env.apiBase]: { target: env.proxyTarget, changeOrigin: true },
    },
  },
});
