// vite.config.js
import { defineConfig } from "vite";
import { readdirSync } from "fs";
import { resolve } from "path";
import nodeRedPlugin from "./vite-plugin-node-red";
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
    // Enable for better debugging. Also set NODE_ENV=development.
    // To use a non-inline sourcemap, some plugin changes are required.
    // sourcemap: "inline",
    rollupOptions: {
      // Dynamically generated multi-entry object.
      input: getEntries(),
      output: {
        entryFileNames: "[name]-[hash].js",
      },
      // DO NOT add @vitejs/plugin-react - it will cause errors with hot reloading,
      // which isn't designed to work.
      plugins: [nodeRedPlugin()],
      // May be necessary to exteralize certain modules
      // external: [...builtinModules],
    },
    assetsDir: "resources",
    outDir: "dist",
  },
});
