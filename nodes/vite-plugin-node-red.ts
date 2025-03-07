import { promises as fs } from "fs";
import path from "node:path";
import type { Plugin } from "vite";
import type { NormalizedOutputOptions, OutputBundle } from "rollup";
import { readFile } from "node:fs/promises";

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
    transform: {
      order: "pre",
      handler: async (code, id) => {
        // Only process HTML files.
        if (!id.endsWith(".html")) return null;

        let html = code;
        // Regex to match <script> tags with a src attribute.
        // Matches tags like:
        // <script ... type="module" ... src="..."></script>
        const scriptRegex =
          /<script\s+([^>]*?)src\s*=\s*['"]([^'"]+)['"]([^>]*?)>(.*?)<\/script>/g;
        let match;

        console.log("Processing HTML file:", id);

        if (
          id ===
          "/Users/sammendelson/Documents/GitHub/biomedical-robot-orchestrator/nodes/nodes/grpc-ping/grpc-ping.html"
        ) {
          console.log("HTML:", html);
        }
        while ((match = scriptRegex.exec(html)) !== null) {
          const [fullMatch, attrBefore, src, attrAfter] = match;
          const combinedAttrs = attrBefore + attrAfter;

          // Only process tags that have type="module"
          if (!/\btype\s*=\s*['"]module['"]/.test(combinedAttrs)) {
            continue;
          }

          console.log("Processing script tag with src:", src);

          // Resolve the file path relative to the current HTML file.
          const filePath = path.resolve(path.dirname(id), src);
          let fileContent;
          try {
            fileContent = await readFile(filePath, "utf8");
          } catch (error) {
            console.error(`Failed to read file at ${filePath}:`, error);
            continue;
          }

          // Use Vite's transformation pipeline to compile the JS file.
          let transformed;
          try {
            transformed = await transformWithEsbuild(fileContent, filePath);
          } catch (error) {
            console.error(`Error transforming file ${filePath}:`, error);
            transformed = { code: fileContent };
          }

          const attrs = (attrBefore + attrAfter).replaceAll(
            `type="module"`,
            `type="text/javascript"`,
          );

          // Create the inline script tag with the transformed code.
          const inlineScriptTag = `<script ${attrs}>${transformed.code}</script>`;

          // Replace the original <script src="..."> tag with the inline version.
          html = html.replace(fullMatch, inlineScriptTag);
        }

        return html;
      },
    },
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
            /(import\s+[^'"]*['"])([^'"]+\.js)(['"])/g,
            (match, p1, modulePath, p3) => `${p1}../.${modulePath}${p3}`,
          );
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
      for (const [fileName, assetInfo] of Object.entries(bundle)) {
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
