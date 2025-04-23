// vite.config.js
import { defineConfig } from "vite";
import { readdirSync } from "fs";
import { resolve } from "path";
import nodeRedPlugin from "./vite-plugin-node-red";
import { builtinModules } from "module";
import react from "@vitejs/plugin-react";

function getEntries(): Record<string, string> {
  const nodesDir = resolve(__dirname, "nodes");
  const entries = {};
  const subdirs = readdirSync(nodesDir, { withFileTypes: true })
    .filter((dirent) => dirent.isDirectory())
    .map((dirent) => dirent.name);

  subdirs.forEach((subdir) => {
    // Each key is the subfolder name and the value is the absolute path to its index.html.
    entries[`${subdir}`] = resolve(`./nodes/${subdir}/${subdir}.html`);
  });

  return entries;
}

export default defineConfig({
  base: "/resources/nodes/",
  mode: "production",
  build: {
    emptyOutDir: true,
    // sourcemap: "inline",
    rollupOptions: {
      // Dynamically generated multi-entry object.
      input: getEntries(),
      output: {
        entryFileNames: "[name]-[hash].js",
      },
      plugins: [nodeRedPlugin()],
      // external: [...builtinModules],
    },
    assetsDir: "resources",
    outDir: "dist",
  },
});
