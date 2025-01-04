/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import fs from "fs";
import path from "path";
import dotenv from "dotenv";

dotenv.config({
  path: path.resolve(__dirname, ".env"),
});

const keyPath = path.resolve(__dirname, "../key.pem");
const certPath = path.resolve(__dirname, "../cert.pem");

let httpsConfig = undefined;

if (fs.existsSync(keyPath) && fs.existsSync(certPath)) {
  const key = fs.readFileSync(keyPath);
  const cert = fs.readFileSync(certPath);
  httpsConfig = {
    key,
    cert,
  };
}

export default defineConfig({
  test: {
    globals: true,
    setupFiles: ["./test-setup.ts"],
    environment: "jsdom",
  },
  server: {
    https: httpsConfig,
    strictPort: true,
    port: 3000,
    proxy: {
      "/api": {
        target: process.env.BACKEND_URL,
        changeOrigin: true,
        rewrite: (path) => path,
        secure: false,
      },
    },
  },
});
