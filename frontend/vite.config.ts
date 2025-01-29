/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import path from "path";
import dotenv from "dotenv";

dotenv.config({
  path: path.resolve(__dirname, ".env"),
});


export default defineConfig({
  test: {
    globals: true,
    setupFiles: ["./test-setup.ts"],
    environment: "jsdom",
  },
  server: {
    strictPort: true,
    port: 3000,
    proxy: {
      "/api": {
        target: process.env.BACKEND_URL,
        changeOrigin: true,
        rewrite: (path) => path,
      },
    },
  },
});
