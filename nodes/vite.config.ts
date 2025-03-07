// vite.config.js
import { defineConfig } from "vite";
import fs from "fs";
import { resolve } from "path";
import nodeRedPlugin from "./vite-plugin-node-red";
import { builtinModules } from "module";

function getEntries(): Record<string, string> {
  const nodesDir = resolve(__dirname, "nodes");
  const entries = {};
  const subdirs = fs
    .readdirSync(nodesDir, { withFileTypes: true })
    .filter((dirent) => dirent.isDirectory())
    .map((dirent) => dirent.name);

  subdirs.forEach((subdir) => {
    // Each key is the subfolder name and the value is the absolute path to its index.html.
    // entries[`${subdir}_nodejsfile`] = resolve(
    //   `./nodes/${subdir}/node/index.ts`,
    // );
    entries[`${subdir}`] = resolve(`./nodes/${subdir}/${subdir}.html`);
  });

  // console.log(entries);

  return entries;
}

export default defineConfig({
  base: "/resources/nodes/",
  build: {
    emptyOutDir: true,
    minify: false,
    rollupOptions: {
      // Dynamically generated multi-entry object.
      input: getEntries(),
      output: {
        entryFileNames: "[name].js",
        // chunkFileNames: "[name].js",
        // assetFileNames: "[name]-[hash][extname]",
      },
      plugins: [nodeRedPlugin()],
      external: [...builtinModules],
    },
    assetsDir: "resources",
    outDir: "dist",
  },
});
