import assert from "node:assert/strict";
import test from "node:test";
import { parseNoteText } from "./note_metadata.mjs";

test("literal trailing quotes survive unquoted YAML titles", () => {
  const note = parseNoteText('---\ntitle: Refactoring the "Garden of Forking Paths"\n---\nBody.');
  assert.equal(note.title, 'Refactoring the "Garden of Forking Paths"');
});

test("quoted and escaped YAML metadata retain their meaning", () => {
  const note = parseNoteText(String.raw`---
title: "Reader's \"evidence\""
description: 'The reader''s example: useful evidence.'
date: '2026-10-22'
tags: [people-analytics, 'causal-inference']
---
Body with [a link](https://example.com).
`);
  assert.equal(note.title, 'Reader\'s "evidence"');
  assert.equal(note.description, "The reader's example: useful evidence.");
  assert.equal(note.date, "2026-10-22");
  assert.deepEqual(note.tags, ["people-analytics", "causal-inference"]);
  assert.equal(note.body, "Body with a link .");
});

test("folded descriptions, block tags and unquoted dates parse as strings", () => {
  const note = parseNoteText(`---
title: Evidence
description: >-
  A longer description
  on two source lines.
date: 2026-10-22
tags:
- people-analytics
- statistics
---
Body.
`);
  assert.equal(note.description, "A longer description on two source lines.");
  assert.equal(note.date, "2026-10-22");
  assert.deepEqual(note.tags, ["people-analytics", "statistics"]);
});

test("missing and malformed frontmatter fail with a useful note label", () => {
  for (const text of ["No frontmatter", "---\ntitle: [unclosed\n---\nBody.",
                      "---\n- a sequence\n---\nBody.", "---\ntags: invalid\n---\nBody."]) {
    assert.throws(() => parseNoteText(text, "broken.md"), /(?:frontmatter|tags).*broken\.md/);
  }
});
