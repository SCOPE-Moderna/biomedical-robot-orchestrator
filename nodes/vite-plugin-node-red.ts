import { promises as fs } from "fs";
import path from "node:path";
import type { Plugin } from "vite";
import type { OutputBundle, NormalizedOutputOptions } from "rollup";
import { c } from "vite/dist/node/moduleRunnerTransport.d-CXw_Ws6P";

export interface VitePluginNodeRedOptions {
  packageName?: string;
  nodesDirectory?: string;
  nodeJsEntrySuffix?: string;
  writePackageJson?: boolean;
}

const defaultOptions: VitePluginNodeRedOptions = {
  packageName: "nodes",
  nodesDirectory: "nodes",
  nodeJsEntrySuffix: "_nodejsfile",
  writePackageJson: true,
};

export default function nodeRedPlugin(opt = defaultOptions): Plugin {
  const pluginOptions = { ...defaultOptions, ...opt };

  return {
    name: "vite-node-red-plugin",
    generateBundle(options, bundle) {
      Object.entries(bundle).forEach(([fileName, file]) => {
        if (file.type === "chunk" && file.facadeModuleId?.endsWith(".html")) {
          // This is FRONTEND js linked from the HTML
          file.fileName = `resources/${fileName}`;
          return;
        }

        if (
          file.type === "chunk" &&
          fileName.endsWith(`${pluginOptions.nodeJsEntrySuffix}.js`)
        ) {
          // Find the HTML by removing pluginOptions.nodeJsEntrySuffix from the file name
          const baseName = fileName
            .split(".")[0]
            .replace(pluginOptions.nodeJsEntrySuffix, "");

          const htmlName = `${pluginOptions.nodesDirectory}/${baseName}/${baseName}.html`;
          if (bundle[htmlName]) {
            // Rename JS file to match HTML (e.g., about.html → about.js)
            file.fileName = htmlName.replace(".html", ".js");
          }

          // Update import path to import from the resources directory (2 levels up)
          file.code = file.code.replace(
            /(import\s+[^'"]*['"])([^'"]+)(['"])/g,
            (match, p1, modulePath, p3) => `${p1}../.${modulePath}${p3}`,
          );
        }
      });
    },
    async writeBundle(
      outputOptions: NormalizedOutputOptions,
      bundle: OutputBundle,
    ): Promise<void> {
      const pkg = {
        name: pluginOptions.packageName,
        version: "1.0.0",
        node_red: {
          nodes: {},
        },
        dependencies: {},
      };

      // Add each output file to package.node_red.nodes
      for (const [fileName, assetInfo] of Object.entries(bundle)) {
        if (assetInfo.type === "chunk" && assetInfo.isEntry) {
          if (!assetInfo.name.endsWith(pluginOptions.nodeJsEntrySuffix)) {
            continue;
          }

          const nodeName = assetInfo.name.slice(
            0,
            -pluginOptions.nodeJsEntrySuffix.length,
          );
          console.log({
            name: assetInfo.name,
            fileName: assetInfo.fileName,
            nodeName,
          });
          // Use the file name as the key and its relative path as the value.
          pkg.node_red.nodes[nodeName] = assetInfo.fileName;
        }
      }

      if (!pluginOptions.writePackageJson) {
        return;
      }

      // Determine the output directory.
      // outputOptions.dir is used when multiple files are generated,
      // or outputOptions.file for single file builds.
      const outDir =
        outputOptions.dir ||
        (outputOptions.file ? path.dirname(outputOptions.file) : "dist");
      const outPackagePath = path.resolve(
        process.cwd(),
        outDir,
        "package.json",
      );

      // Write the new package.json to the output directory.
      try {
        await fs.writeFile(
          outPackagePath,
          JSON.stringify(pkg, null, 2),
          "utf8",
        );
      } catch (err) {
        this.error(`Error writing package.json: ${err}`);
      }
    },
  };
}
