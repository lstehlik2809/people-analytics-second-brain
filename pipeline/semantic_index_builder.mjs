import { readdirSync, readFileSync, writeFileSync, statSync } from "node:fs";
import path from "node:path";
import { parseNoteText } from "./note_metadata.mjs";
import { CHUNK_CHARS, CHUNK_OVERLAP, MAX_CHUNKS, chunkBody } from "./semantic_text.mjs";

export const MODEL = "Xenova/all-MiniLM-L6-v2";
// Bump the schema/config contract when pooling, normalization, model revision,
// rounding, or other vector-generation semantics change, even if text is equal.
const INDEX_SCHEMA = 3;
const DIMS = 384;

export function isReusableIndex(cached, expected) {
  if (!cached || typeof cached !== "object") return false;
  for (const key of ["schema", "model", "dims", "vectorCount", "passageCount"]) {
    if (cached[key] !== expected[key]) return false;
  }
  if (!cached.chunking ||
      Object.keys(cached.chunking).length !== Object.keys(expected.chunking).length ||
      !Object.keys(expected.chunking).every(key => cached.chunking[key] === expected.chunking[key])) return false;
  if (!Array.isArray(cached.posts) || cached.posts.length !== expected.posts.length) return false;
  return expected.posts.every((post, index) => {
    const previous = cached.posts[index];
    if (!previous || typeof previous !== "object") return false;
    for (const key of ["slug", "title", "description", "date", "tags", "passages"]) {
      if (JSON.stringify(previous[key]) !== JSON.stringify(post[key])) return false;
    }
    return Array.isArray(previous.vecs) && previous.vecs.length === post.passages.length &&
      previous.vecs.every(vector => Array.isArray(vector) && vector.length === expected.dims &&
        vector.every(value => typeof value === "number" && Number.isFinite(value)));
  });
}

export async function buildSemanticIndex({ notesDir, output, createExtractor, log = console.log }) {
  const files = readdirSync(notesDir).filter(file => file.endsWith(".md")).sort();
  let passageCount = 0;
  let cappedCount = 0;
  const posts = files.map(file => {
    const slug = file.replace(/\.md$/, "");
    const note = parseNoteText(readFileSync(path.join(notesDir, file), "utf-8"), file);
    const bodyChunks = chunkBody(note.body);
    const uncappedCount = note.body.length <= CHUNK_CHARS
      ? (note.body.length ? 1 : 0)
      : Math.ceil((note.body.length - CHUNK_CHARS) / (CHUNK_CHARS - CHUNK_OVERLAP)) + 1;
    if (uncappedCount > MAX_CHUNKS) cappedCount++;
    passageCount += bodyChunks.length;
    return {
      slug,
      title: note.title,
      description: note.description,
      date: note.date,
      tags: note.tags,
      passages: [`${note.title}. ${note.description} Topics: ${note.tags.join(", ")}`, ...bodyChunks],
    };
  });
  const expected = {
    schema: INDEX_SCHEMA,
    model: MODEL,
    dims: DIMS,
    vectorCount: posts.reduce((sum, post) => sum + post.passages.length, 0),
    passageCount,
    chunking: { chars: CHUNK_CHARS, overlap: CHUNK_OVERLAP, maxChunks: MAX_CHUNKS, overflow: "evenly-spaced" },
    posts,
  };
  let cached;
  try {
    cached = JSON.parse(readFileSync(output, "utf-8"));
  } catch {
    // A missing/unreadable/invalid index takes the normal generation path.
  }
  if (isReusableIndex(cached, expected)) {
    log(`Reused browser index: ${posts.length} notes, ${expected.vectorCount} vectors; inputs unchanged, no model inference or file write.`);
    return { reused: true, noteCount: posts.length, vectorCount: expected.vectorCount };
  }

  log(`Embedding ${files.length} notes with ${MODEL}...`);
  const extractor = await createExtractor();
  for (const [index, post] of posts.entries()) {
    const out = await extractor(post.passages, { pooling: "mean", normalize: true });
    const [rows, dims] = out.dims;
    if (rows !== post.passages.length || dims !== DIMS || out.data.length !== rows * dims) {
      throw new Error(`Unexpected embedding shape for ${post.slug}`);
    }
    post.vecs = Array.from({ length: rows }, (_, row) =>
      Array.from(out.data.slice(row * dims, (row + 1) * dims), value => +value.toFixed(4)));
    if ((index + 1) % 50 === 0) log(`  ${index + 1}/${files.length}`);
  }
  writeFileSync(output, JSON.stringify(expected));
  log(`done: ${posts.length} notes, ${passageCount} body passages, ${expected.vectorCount} total vectors, ${cappedCount} capped notes, ${(statSync(output).size / 1e6).toFixed(1)} MB -> ${output}`);
  return { reused: false, noteCount: posts.length, vectorCount: expected.vectorCount };
}
