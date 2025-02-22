import { resolve } from 'node:path';
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
    root: resolve(__dirname, './src'),
    publicDir: '../web_static',
    base: '/static',
    plugins: [react(), tailwindcss()],
    build: {
        outDir: resolve(__dirname, './build'),
        manifest: 'manifest.json',
        assetsDir: 'bundled',
        emptyOutDir: true,
        copyPublicDir: false,
        rollupOptions: {
            input: ['./src/index.tsx', './src/styles/app.css']
        }
    },
    resolve: {
        alias: {
            '@': resolve(__dirname, './src')
        }
    }
});