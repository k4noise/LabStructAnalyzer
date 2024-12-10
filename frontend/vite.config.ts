import { defineConfig } from 'vite';
import fs from 'fs';
import path from 'path';

const keyPath = path.resolve(__dirname, '../key.pem');
const certPath = path.resolve(__dirname, '../cert.pem');

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
  server: {
    https: httpsConfig,
    strictPort: true,
    port: 3000,
  },
});