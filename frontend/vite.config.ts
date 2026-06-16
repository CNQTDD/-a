import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: "happy-dom",
    globals: true,
    include: ["tests/unit/**/*.test.ts"],
    exclude: ["tests/e2e/**"],
  },
});
