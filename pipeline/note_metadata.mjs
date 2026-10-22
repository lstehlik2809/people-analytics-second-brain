import { parse } from "yaml";
import { cleanBody } from "./semantic_text.mjs";

export function parseNoteText(text, label = "note") {
  const front = text.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
  if (!front) throw new Error(`Missing YAML frontmatter: ${label}`);
  let metadata;
  try {
    metadata = parse(front[1]);
  } catch (error) {
    throw new Error(`Invalid YAML frontmatter in ${label}: ${error.message}`);
  }
  if (!metadata || typeof metadata !== "object" || Array.isArray(metadata)) {
    throw new Error(`YAML frontmatter must be a mapping: ${label}`);
  }
  const tags = metadata.tags ?? [];
  if (!Array.isArray(tags) || !tags.every(tag => typeof tag === "string")) {
    throw new Error(`YAML tags must be a list of strings: ${label}`);
  }
  const value = key => String(metadata[key] ?? "").trim();
  return {
    title: value("title"),
    description: value("description"),
    date: value("date"),
    tags,
    body: cleanBody(text.slice(front[0].length)),
  };
}
