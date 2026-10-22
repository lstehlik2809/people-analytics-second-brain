# Ludek's People Analytics Second Brain 🧠

A public, Obsidian-style second brain built from the <!--N-->224<!--/N--> posts on
[my people analytics blog](https://blog-about-people-analytics.netlify.app/) —
browsable as an interactive knowledge graph, full-text searchable, and
machine-readable for AI agents.

**Live site:** https://lstehlik2809.github.io/people-analytics-second-brain

## How it works

```
People_Analytics_Blog/_posts/*.Rmd        (source of truth)
        │  pipeline/convert.py            → clean markdown notes + assets + figures
        ▼
vault/posts/*.md                          (the second brain)
        │  pipeline/embed_link.py         → chunked full-note embeddings + semantic "Related notes"
        │  pipeline/build_llms.py         → llms.txt / llms-full.txt for AI agents
        │  pipeline/build_semantic_index.mjs → chunked hybrid browser search index
        ▼
site/ (Quartz 5)                          → static site with graph view, search, tag pages
        │  GitHub Actions (deploy.yml)
        ▼
GitHub Pages
```

- **For people:** graph view, backlinks, tags, `Ctrl+K` full-text search, and
  [in-browser hybrid search](https://lstehlik2809.github.io/people-analytics-second-brain/semantic-search.html)
  (BM25 + transformers.js/MiniLM, no server). Hybrid retrieval and related-note
  matching both index overlapping passages across each note's cleaned prose,
  so exact terminology and semantic paraphrases can surface later sections of
  long posts.
- **For AI agents:** a public [MCP server](https://people-analytics-brain-mcp.ludek-stehlik.workers.dev)
  (`https://people-analytics-brain-mcp.ludek-stehlik.workers.dev/mcp`, Streamable HTTP, no auth) with
  `search_notes` / `get_note` / `list_notes` / `list_tags` tools, plus
  [`/llms.txt`](https://lstehlik2809.github.io/people-analytics-second-brain/llms.txt)
  (index) and [`/llms-full.txt`](https://lstehlik2809.github.io/people-analytics-second-brain/llms-full.txt)
  (complete corpus). The worker ([mcp-server/](mcp-server/)) fetches the corpus from the
  live site, so it needs no redeploys when content changes.

## Update in the cloud

GitHub Actions can fetch the published blog source, regenerate the second brain,
verify it, and deploy it without a Windows computer. In repository **Settings →
Secrets and variables → Actions**, set the `OPENAI_API_KEY` secret and, optionally,
the `OPENAI_EMBEDDING_MODEL` variable (default: `text-embedding-3-large`). Enable
Actions and configure Pages to use GitHub Actions. The update job requests
`contents: write` for its scoped publish step.
The key is available only to the embedding step; only the ignored embedding
vectors are cached. The first cloud run needs to embed the corpus. Later runs
reuse that cache and embed only changed notes.
The browser index also reuses its existing file when all metadata, ordered
passages and model/chunking settings match and its vectors are valid. This avoids
CPU rounding differences creating content commits on unchanged runs. Changes to
pooling, normalization, model revision or other vector-generation semantics must
invalidate the index schema/configuration contract before reusing old vectors.

Run **Actions → Update second brain in the cloud → Run workflow** on `main`:

- `preview` (default) generates and verifies everything, then provides a seven-day
  downloadable artifact. It makes no content commit and does not deploy.
- `publish` verifies and builds before committing only the generated paths and
  pushing to `main`. The same run deploys that exact new commit. If generated
  content is unchanged, it creates no content commit or deployment.

For direct workflow dispatch, pass `mode` and optionally a fresh canonical UUID
as `request_id`. The UUID appears in the Actions run title, summary and preview
report, so callers can identify their exact run even when several requests use
the same commit. For example, dispatch with `{"mode":"preview", "request_id":
"a84ea198-2302-442a-869b-06e678c489da"}`. Omit `request_id` for ordinary manual
runs; the updater generates one internally. Reuse neither a UUID nor another
request's run when checking completion.

From a connected assistant that can update GitHub files, submit a fresh UUID in
the fixed `.github/brain-update-request.json` file on `main`:

```json
{"mode": "publish", "request_id": "a84ea198-2302-442a-869b-06e678c489da"}
```

Generate a new UUID for each request. The file accepts exactly `mode` and
`request_id`, with no commands, source references or credentials. A request-file
update itself creates a control commit, including for `preview`; use workflow
dispatch when preview must create **no commit at all**. A request-file-only
commit does not run the ordinary Pages deployment. The `update-second-brain`
Codex skill and its private plugin use this cloud route; the local `update.ps1`
route remains available.

Follow the Actions run for the exact dispatch or request commit. Its summary
reports the blog source SHA, note count and changed slugs; deployment verifies
the live revision marker and public exports. GitHub can supersede an older
pending request when several arrive together, so a cancelled run is not evidence
that that request completed. Read status without editing the request file.

If verification fails, inspect the failed step before submitting a new request.
If `main` advances during generation, start a fresh update from `main`; publication
never force-pushes. If content was pushed but deployment failed, use **Re-run
failed jobs** on that run.
A subsequent no-change update intentionally does not redeploy. Never put keys in
the request, repository files, preview artifacts or manual cache uploads.
