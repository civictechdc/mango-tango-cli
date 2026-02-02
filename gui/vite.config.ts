import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import checker from "vite-plugin-checker";

export default defineConfig({
  plugins: [vue({}), checker({ vueTsc: true, typescript: true })],
  build: {
    cssCodeSplit: true,
    outDir: "./components/dist",
    lib: {
      entry: {
        UploadButton: "./components/upload/UploadButton.vue",
      },
      formats: ["es"],
      fileName: (_, entryName): string => `${entryName}.js`,
      name: "vue_vite",
    },
    minify: false,
    rollupOptions: {
      external: ["vue"],
      output: {
        entryFileNames: `[name].js`,
        chunkFileNames: `[name].js`,
        assetFileNames: `[name].[ext]`,
      },
    },
  },
});
