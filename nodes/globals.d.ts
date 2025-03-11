import { RED } from "node-red__editor-client";

export {}; // This ensures the file is treated as a module

declare global {
  const RED: RED;
}
