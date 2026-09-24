import base64
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import convert


class EmbeddedFigureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def data_uri(data=b"embedded chart"):
        payload = base64.b64encode(data).decode("ascii")
        return f"data:image/png;base64,{payload}"

    def test_extracts_only_embedded_images_inside_knitr_figure(self):
        uri = self.data_uri()
        html = (
            f'<article><p><img src="{uri}" alt="ordinary"></p>'
            '<pre>plot(1)</pre>'
            f'<div class="figure"><img src="{uri}" '
            'aria-label="Generated chart"></div></article>'
        )
        (self.root / "post.html").write_text(html, encoding="utf-8")

        figures = convert.extract_generated_figures(self.root, "post")

        self.assertEqual(figures, [("plot(1)", uri, "Generated chart")])

    def test_decodes_and_injects_embedded_figure_after_matching_code(self):
        image = b"embedded chart bytes"
        uri = self.data_uri(image)
        asset_dir = self.root / "assets"
        body = "Before\n\n```r\nplot(1)\n```\n\nAfter"

        result = convert.inject_figures(
            body,
            [("plot(1)", uri, "Generated chart")],
            self.root,
            asset_dir,
            "post",
            [],
        )

        expected = "![Generated chart](./post/generated-figure-01.png)"
        self.assertIn("```r\nplot(1)\n```\n\n" + expected, result)
        self.assertEqual(
            (asset_dir / "generated-figure-01.png").read_bytes(), image)

    def test_embedded_figure_marker_targets_affected_html(self):
        uri = self.data_uri()
        generated = (
            f'<div class="figure"><img src="{uri}" alt="chart"></div>'
        ).encode()
        ordinary = f'<p><img src="{uri}" alt="ordinary"></p>'.encode()

        self.assertIsNotNone(convert.EMBEDDED_FIGURE_RE.search(generated))
        self.assertIsNone(convert.EMBEDDED_FIGURE_RE.search(ordinary))

    def test_refreshes_changed_external_figure_asset(self):
        source_dir = self.root / "post_files" / "figure-html"
        source_dir.mkdir(parents=True)
        source = source_dir / "chart.png"
        source.write_bytes(b"new chart")
        asset_dir = self.root / "assets"
        asset_dir.mkdir()
        (asset_dir / "chart.png").write_bytes(b"old chart")

        convert.inject_figures(
            "```r\nplot(1)\n```",
            [("plot(1)", "post_files/figure-html/chart.png", "Chart")],
            self.root,
            asset_dir,
            "post",
            [],
        )

        self.assertEqual((asset_dir / "chart.png").read_bytes(), b"new chart")

    def test_copies_local_html_attachment_and_rewrites_embed_and_download(self):
        files_dir = self.root / "files"
        files_dir.mkdir()
        attachment = files_dir / "carousel.pdf"
        attachment.write_bytes(b"pdf bytes")
        asset_dir = self.root / "assets"
        body = (
            '<object data="files/carousel.pdf" type="application/pdf">\n'
            '  <a href="files/carousel.pdf" download>Download</a>\n'
            '</object>'
        )

        result = convert.convert_body(
            body, self.root, asset_dir, "post", [])

        target = "./post/carousel.pdf"
        self.assertEqual(result.count(target), 2)
        self.assertEqual((asset_dir / "carousel.pdf").read_bytes(), b"pdf bytes")

    def test_copies_local_media_source_and_rewrites_video_url(self):
        source = self.root / "simulation.mp4"
        source.write_bytes(b"video bytes")
        asset_dir = self.root / "assets"
        body = (
            '<video controls><source src="simulation.mp4" '
            'type="video/mp4"></video>'
        )

        result = convert.convert_body(
            body, self.root, asset_dir, "post", [])

        self.assertIn('src="./post/simulation.mp4"', result)
        self.assertEqual((asset_dir / "simulation.mp4").read_bytes(), b"video bytes")

    def test_converts_video_only_vembedr_chunk_to_youtube_embed(self):
        body = (
            'Before\n\n```{r echo=FALSE}\n\n'
            'library(vembedr)\n'
            'vembedr::embed_youtube("OwKj-wgXteo")\n\n'
            '```\n\nAfter'
        )

        result = convert.convert_body(body, self.root, self.root / "assets", "post", [])

        self.assertIn('src="https://www.youtube.com/embed/OwKj-wgXteo"', result)
        self.assertNotIn("library(vembedr)", result)
        self.assertNotIn("```r", result)

    def test_keeps_vembedr_chunk_with_other_code(self):
        body = (
            '```{r}\n'
            'vembedr::embed_youtube("OwKj-wgXteo")\n'
            'print("more work")\n'
            '```'
        )

        result = convert.convert_body(body, self.root, self.root / "assets", "post", [])

        self.assertIn('```r', result)
        self.assertNotIn('<iframe', result)

    def test_extracts_and_injects_plotly_widget_in_a_local_iframe(self):
        library_dir = self.root / "post_files" / "plotly-main-2.11.1"
        library_dir.mkdir(parents=True)
        library = library_dir / "plotly-latest.min.js"
        library.write_text("window.Plotly = {};", encoding="utf-8")
        widget = {
            "x": {
                "data": [{"x": [1, 2], "y": [3, 4], "type": "scatter"}],
                "layout": {"height": 480},
                "config": {"displayModeBar": False},
            },
            "evals": [],
            "jsHooks": [],
        }
        (self.root / "post.html").write_text(
            '<pre>plot(1)</pre>'
            '<div id="widget" class="plotly html-widget"></div>'
            f'<script data-for="widget" type="application/json">'
            f'{convert.json.dumps(widget)}</script>'
            '<script src="post_files/plotly-main-2.11.1/plotly-latest.min.js"></script>',
            encoding="utf-8",
        )

        widgets = convert.extract_plotly_widgets(self.root, "post")
        result = convert.inject_plotly_widgets(
            "```r\nplot(1)\n```", widgets, self.root, self.root / "assets",
            "post", [],
        )

        self.assertIn('srcdoc="', result)
        self.assertIn('Plotly.newPlot', result)
        self.assertIn('responsive:true', result)
        self.assertIn('./post/plotly-widget-01.min.js', result)
        self.assertEqual(
            (self.root / "assets" / "plotly-widget-01.min.js").read_text(
                encoding="utf-8"),
            "window.Plotly = {};",
        )

    def test_table_preview_bounds_large_rows_and_preserves_all_wide_columns(self):
        columns = [[f"value-{col}-{row}" for row in range(10000)] for col in range(48)]
        columns[0][0] = "<script>alert(1)</script> &amp; safe"
        payload = {"x": {"data": columns, "container": "<table><thead><tr>" +
                   "".join(f"<th>Column {col}</th>" for col in range(48)) +
                   "</tr></thead></table>"}}
        result = convert.render_table_preview(payload, "https://example.com/original")
        self.assertIn("Showing 20 of 10,000 rows and all 48 columns", result)
        self.assertEqual(result.count("<tr>"), 21)
        self.assertEqual(result.count("<th>"), 48)
        self.assertIn("value-47-19", result)
        self.assertNotIn("value-47-20", result)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt; &amp; safe", result)
        self.assertIn("overflow-x:auto", result)

    def test_bad_table_and_missing_specialty_dependency_warn_without_iframe(self):
        (self.root / "post.html").write_text(
            '<pre>DT::datatable(x)</pre><div id="table" class="datatables html-widget"></div>'
            '<script data-for="table" type="application/json">'
            '{"x":{"data":[[1,2],[3]],"container":"<table><thead><tr><th>A</th><th>B</th></tr></thead></table>"}}'
            '</script><div id="graph" class="forceNetwork html-widget"></div>'
            '<script data-for="graph" type="application/json">{"x":{"links":{},"nodes":{}}}</script>'
            '<script src="post_files/htmlwidgets-1/htmlwidgets.js"></script>', encoding="utf-8")
        warnings = []
        widgets = convert.extract_output_widgets(self.root, "post", warnings)
        result = convert.inject_output_widgets("```r\nDT::datatable(x)\n```", widgets,
                                               self.root, self.root / "assets", "post",
                                               "https://example.com", warnings)
        self.assertNotIn("<iframe", result)
        self.assertNotIn("data-table-preview", result)
        self.assertTrue(any("invalid datatables" in w for w in warnings))
        self.assertTrue(any("missing or invalid forceNetwork dependency" in w for w in warnings))

    def test_packages_specialty_widget_with_local_runtime(self):
        library = self.root / "post_files" / "htmlwidgets-1" / "htmlwidgets.js"
        library.parent.mkdir(parents=True)
        library.write_text("window.HTMLWidgets={};", encoding="utf-8")
        binding = self.root / "post_files" / "forceNetwork-binding-1" / "forceNetwork.js"
        binding.parent.mkdir(parents=True)
        binding.write_text("window.bound=true;", encoding="utf-8")
        (self.root / "post.html").write_text(
            '<pre>networkD3::forceNetwork(x)</pre>'
            '<div id="graph" class="forceNetwork html-widget" style="height:384px"></div>'
            '<script data-for="graph" type="application/json">{"x":{"links":{},"nodes":{}}}</script>'
            '<script src="post_files/htmlwidgets-1/htmlwidgets.js"></script>'
            '<script src="post_files/forceNetwork-binding-1/forceNetwork.js"></script>',
            encoding="utf-8")
        warnings = []
        widgets = convert.extract_output_widgets(self.root, "post", warnings)
        result = convert.inject_output_widgets("```r\nnetworkD3::forceNetwork(x)\n```",
                                               widgets, self.root, self.root / "assets",
                                               "post", "https://example.com", warnings)
        self.assertFalse(warnings)
        self.assertIn('src="./post/widget-forcenetwork-01.htm"', result)
        frame = (self.root / "assets" / "widget-forcenetwork-01.htm").read_text()
        self.assertIn('data-for="graph"', frame)
        emitted_ref = "widget-deps/forcenetwork/post_files/forcenetwork-binding-1/forcenetwork.js"
        self.assertIn(emitted_ref, frame)
        self.assertEqual((self.root / "assets" / "widget-deps" / "forcenetwork" / "post_files" /
                          "forcenetwork-binding-1" / "forcenetwork.js").read_text(),
                         "window.bound=true;")
        current = self.root / "assets"
        for part in emitted_ref.split("/"):
            self.assertIn(part, [entry.name for entry in current.iterdir()])
            current /= part

    def test_preserves_existing_related_links_when_rebuilding(self):
        old = "before\n<!-- RELATED:BEGIN -->\n## Related notes\n- [[other|Other]]\n<!-- RELATED:END -->\n"
        new = "after\n<!-- RELATED:BEGIN -->\n<!-- RELATED:END -->\n"
        self.assertIn("- [[other|Other]]", convert.preserve_related_block(new, old))
        self.assertTrue(convert.preserve_related_block(new, old).startswith("after"))


if __name__ == "__main__":
    unittest.main()
