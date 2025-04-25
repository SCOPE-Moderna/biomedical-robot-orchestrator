import { promises as fs } from "fs";
import * as path from "node:path";
import { type Plugin } from "vite";
import type { NormalizedOutputOptions, OutputBundle } from "rollup";
import { readFile } from "node:fs/promises";

export interface VitePluginNodeRedOptions {
  packageName?: string;
  nodesDirectory?: string;
  writePackageJson?: boolean;
}

const defaultOptions: VitePluginNodeRedOptions = {
  packageName: "nodes",
  nodesDirectory: "nodes",
  writePackageJson: true,
};

export default function nodeRedPlugin(opt = defaultOptions): Plugin {
  const pluginOptions = { ...defaultOptions, ...opt };

  return {
    name: "vite-node-red-plugin",
    generateBundle(_, bundle) {
      Object.entries(bundle).forEach(([fileName, file]) => {
        if (file.type === "chunk") {
          // Prepend resources/ to all JS files as they have to go into
          // the resources/ folder for Node-RED to serve them.
          file.fileName = `resources/${fileName}`;
        }
      });
    },
    async writeBundle(
      outputOptions: NormalizedOutputOptions,
      bundle: OutputBundle,
    ): Promise<void> {
      // read package.json
      const packageJsonPath = path.resolve(process.cwd(), "package.json");
      const packageJson = JSON.parse(await readFile(packageJsonPath, "utf8"));

      const pkg = {
        name: pluginOptions.packageName,
        version: "1.0.0",
        "node-red": {
          nodes: {},
        },
        dependencies: packageJson.dependencies,
        devDependencies: packageJson.devDependencies,
      };

      // Add each output file to package.node_red.nodes
      for (const [_, assetInfo] of Object.entries(bundle)) {
        if (
          assetInfo.type === "asset" &&
          assetInfo.fileName.endsWith(".html")
        ) {
          const nodeName = path.parse(assetInfo.fileName).name;

          pkg["node-red"].nodes[nodeName] = assetInfo.fileName.replace(
            ".html",
            ".js",
          );
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
