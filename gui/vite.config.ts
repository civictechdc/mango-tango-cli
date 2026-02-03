import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import checker from "vite-plugin-checker";
import * as actualVue from "vue";

export default defineConfig({
  plugins: [
    {
      name: "inline-vue-shim",
      enforce: "pre" as const,
      resolveId(id: string) {
        if (id === "vue") {
          return "virtual:vue-shim";
        }
      },
      load(id: string) {
        if (id === "virtual:vue-shim") {
          const lines: string[] = ["const Vue = window.Vue;"];
          for (const exportName of Object.keys(actualVue)) {
            lines.push(`export const ${exportName} = Vue.${exportName};`);
          }
          lines.push("export default Vue;");
          return lines.join("\n");
        }
      },
    },
    vue(),
  ],
  define: {
    "process.env.NODE_ENV": JSON.stringify("production"),
  },
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
  },
});
