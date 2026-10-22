import assert from "node:assert/strict";
import test from "node:test";
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, statSync, utimesSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { buildSemanticIndex, isReusableIndex } from "./semantic_index_builder.mjs";

function fixture(t) {
  const scratchRoot = path.resolve(tmpdir());
  const directory = mkdtempSync(path.join(scratchRoot, "brain-index-"));
  t.after(() => {
    const target = path.resolve(directory);
    assert.equal(path.dirname(target), scratchRoot);
    assert.ok(path.basename(target).startsWith("brain-index-"));
    rmSync(target, { recursive: true, force: true });
  });
  const notesDir = path.join(directory, "notes");
  mkdirSync(notesDir);
  const notePath = path.join(notesDir, "evidence.md");
  writeFileSync(notePath, '---\ntitle: Evidence\ndescription: A fixture.\ndate: "2026-10-22"\ntags: [statistics]\n---\nReliable evidence.\n');
  const output = path.join(directory, "semantic_index.json");
  let constructions = 0;
  const inputs = [];
  const createExtractor = async () => {
    constructions++;
    return async (passages, options) => {
      inputs.push({ passages, options });
      return { dims: [passages.length, 384], data: new Float32Array(passages.length * 384).fill(0.125) };
    };
  };
  return { notesDir, notePath, output, createExtractor, inputs,
    build: () => buildSemanticIndex({ notesDir, output, createExtractor, log() {} }),
    constructions: () => constructions };
}

test("unchanged inputs reuse exact file bytes without constructing an extractor", async t => {
  const f = fixture(t);
  assert.equal((await f.build()).reused, false);
  assert.equal(f.constructions(), 1);
  assert.deepEqual(f.inputs[0], {
    passages: ["Evidence. A fixture. Topics: statistics", "Reliable evidence."],
    options: { pooling: "mean", normalize: true },
  });
  const bytes = readFileSync(f.output);
  utimesSync(f.output, new Date("2000-01-01"), new Date("2000-01-01"));
  const modified = statSync(f.output).mtimeMs;
  for (let attempt = 0; attempt < 2; attempt++) {
    const result = await buildSemanticIndex({ notesDir: f.notesDir, output: f.output, log() {},
      createExtractor() { throw new Error("Unchanged index constructed an extractor"); } });
    assert.equal(result.reused, true);
    assert.deepEqual(readFileSync(f.output), bytes);
    assert.equal(statSync(f.output).mtimeMs, modified);
  }
});

test("changed metadata or cleaned passages rebuild using the current inputs", async t => {
  const f = fixture(t);
  await f.build();
  writeFileSync(f.notePath, readFileSync(f.notePath, "utf8").replace('"2026-10-22"', '"2026-10-23"'));
  assert.equal((await f.build()).reused, false);
  assert.equal(JSON.parse(readFileSync(f.output)).posts[0].date, "2026-10-23");
  writeFileSync(f.notePath, readFileSync(f.notePath, "utf8").replace("Reliable evidence.", "New evidence."));
  assert.equal((await f.build()).reused, false);
  assert.deepEqual(f.inputs.at(-1).passages, ["Evidence. A fixture. Topics: statistics", "New evidence."]);
  assert.equal(f.constructions(), 3);
});

test("every input/configuration field and ordered passage list controls reuse", async t => {
  const f = fixture(t);
  await f.build();
  const valid = JSON.parse(readFileSync(f.output));
  const mutations = [
    x => x.schema++, x => x.model = "different-model", x => x.dims = 12,
    x => x.vectorCount++, x => x.passageCount++,
    x => x.chunking.chars++, x => x.chunking.overlap++, x => x.chunking.maxChunks++,
    x => x.chunking.overflow = "different", x => x.chunking = null,
    x => x.posts[0].slug = "different", x => x.posts[0].title = "Different",
    x => x.posts[0].description = "Different", x => x.posts[0].date = "2026-10-23",
    x => x.posts[0].tags.push("new-tag"), x => x.posts[0].passages.reverse(),
    x => x.posts[0].passages[1] = "Changed passage", x => x.posts.push(x.posts[0]),
  ];
  assert.equal(isReusableIndex(valid, valid), true);
  for (const mutate of mutations) {
    const altered = structuredClone(valid);
    mutate(altered);
    assert.equal(isReusableIndex(altered, valid), false);
  }
});

test("missing/invalid JSON and malformed vector structures take the rebuild path", async t => {
  const f = fixture(t);
  await f.build();
  const valid = JSON.parse(readFileSync(f.output));
  const mutations = [
    x => x.posts = null, x => x.posts[0] = null, x => x.posts[0].vecs = null,
    x => x.posts[0].vecs.pop(), x => x.posts[0].vecs[0] = null,
    x => x.posts[0].vecs[0].pop(), x => x.posts[0].vecs[0][0] = "0.1",
    x => x.posts[0].vecs[0][0] = null,
  ];
  writeFileSync(f.output, "{invalid JSON");
  assert.equal((await f.build()).reused, false);
  for (const mutate of mutations) {
    const altered = structuredClone(valid);
    mutate(altered);
    writeFileSync(f.output, JSON.stringify(altered));
    assert.equal((await f.build()).reused, false);
    assert.equal(isReusableIndex(JSON.parse(readFileSync(f.output)), valid), true);
  }
  for (const value of [NaN, Infinity, -Infinity]) {
    const altered = structuredClone(valid);
    altered.posts[0].vecs[0][0] = value;
    assert.equal(isReusableIndex(altered, valid), false);
  }
  assert.equal(f.constructions(), 2 + mutations.length);
});
