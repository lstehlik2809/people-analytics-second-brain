import test from "node:test"
import assert from "node:assert/strict"
import { CrawlLinks } from "@quartz-community/crawl-links"

test("PDF object and download resolve to the same published asset on project pages", () => {
  const properties = {
    data: "./the-coincidence-audit/The_Coincidence_Audit.pdf",
    type: "application/pdf",
    style: "width:100%;height:1200px",
    ariaLabel: "Comic",
  }
  const link = { href: properties.data }
  const remote = { data: "https://example.com/Comic.pdf" }
  const tree = {
    type: "root",
    children: [
      { type: "element", tagName: "object", properties, children: [] },
      { type: "element", tagName: "a", properties: link, children: [] },
      { type: "element", tagName: "object", properties: remote, children: [] },
    ],
  }
  const transform = CrawlLinks({ markdownLinkResolution: "shortest" })
    .htmlPlugins({ allSlugs: ["posts/the-coincidence-audit", "posts/the-coincidence-audit/the_coincidence_audit.pdf"] })[0]()
  transform(tree, { data: { slug: "posts/the-coincidence-audit" } })
  assert.equal(properties.data, "../posts/the-coincidence-audit/the_coincidence_audit.pdf")
  assert.equal(properties.data, link.href)
  assert.equal(new URL(properties.data, "https://example.com/brain/posts/the-coincidence-audit").pathname,
    "/brain/posts/the-coincidence-audit/the_coincidence_audit.pdf")
  assert.equal(properties.style, "width:100%;height:1200px")
  assert.equal(properties.ariaLabel, "Comic")
  assert.equal(remote.data, "https://example.com/Comic.pdf")
})
