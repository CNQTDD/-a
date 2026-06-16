import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  use: {
    baseURL: "http://127.0.0.1:5173",
    trace: "on-first-retry",
  },
  webServer: [
    {
      command:
        '"C:\\Users\\Administrator\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\node\\bin\\node.exe" tests\\helpers\\run-child.mjs node_modules\\vite\\bin\\vite.js --host 127.0.0.1 --port 5173 --strictPort',
      url: "http://127.0.0.1:5173",
      reuseExistingServer: true,
      timeout: 120000,
      env: {
        VITE_API_BASE_URL: "http://127.0.0.1:5184",
      },
    },
    {
      command:
        '"C:\\Users\\Administrator\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\node\\bin\\node.exe" tests\\helpers\\run-child.mjs tests\\mock-api\\server.mjs',
      url: "http://127.0.0.1:5184",
      reuseExistingServer: true,
      timeout: 120000,
      env: {
        MOCK_API_PORT: "5184",
      },
    },
  ],
});
