import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "md2html.py"


def render(md):
    return subprocess.run([sys.executable, str(SCRIPT)], input=md, capture_output=True, text=True, check=True).stdout


class Md2HtmlTest(unittest.TestCase):
    def test_unclosed_fence_keeps_content(self):
        self.assertIn("<pre><code>lost line</code></pre>", render("before\n```\nlost line\n"))

    def test_quote_in_url_stays_inside_href(self):
        out = render('[x](https://a.com/"onclick="x)\n')
        self.assertIn('href="https://a.com/&quot;onclick=&quot;x"', out)
        self.assertNotIn(' onclick=', out)

    def test_parens_in_url_stay_in_href(self):
        out = render("[x](https://en.wikipedia.org/wiki/Foo_(bar))\n")
        self.assertIn('href="https://en.wikipedia.org/wiki/Foo_(bar)"', out)
        self.assertIn(">x</a></p>", out)  # no stray ")" after the link

    def test_nested_bullets(self):
        self.assertIn(
            "<ul><li>a\n<ul><li>b\n</li></ul>\n</li><li>c\n</li></ul>",
            render("- a\n  - b\n- c\n"),
        )

    def test_nested_bullets_two_deep_and_back(self):
        self.assertIn(
            "<ul><li>a\n<ul><li>b\n<ul><li>c\n</li></ul>\n</li></ul>\n</li><li>d\n</li></ul>",
            render("- a\n  - b\n    - c\n- d\n"),
        )

    def test_non_ascii_survives_textutil(self):
        # textutil reads undeclared HTML as Latin-1, so "café" pasted as "cafÃ©"
        with tempfile.TemporaryDirectory() as d:
            html = Path(d) / "s.html"
            html.write_text(render("café “quoted”\n"), encoding="utf-8")
            txt = Path(d) / "s.txt"
            subprocess.run(["textutil", "-convert", "txt", "-format", "html", "-output", str(txt), str(html)], check=True)
            self.assertIn("café “quoted”", txt.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
