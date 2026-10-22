// Build the client-side hybrid index with the same passage text and MiniLM model
// as the browser. Reuse a valid, unchanged index to avoid inference-rounding drift.
// Usage: node pipeline/build_semantic_index.mjs

import { fileURLToPath } from "node:url";
import path from "node:path";
import { buildSemanticIndex, MODEL } from "./semantic_index_builder.mjs";

const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
await buildSemanticIndex({
  notesDir: path.join(ROOT, "vault", "posts"),
  output: path.join(ROOT, "pipeline", "cache", "semantic_index.json"),
  createExtractor: async () => {
    const { pipeline } = await import("@huggingface/transformers");
    return pipeline("feature-extraction", MODEL);
  },
});
