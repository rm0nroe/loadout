import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "md2html.py"


def render(md):
    return subprocess.run([sys.executable, str(SCRIPT)], input=md, capture_output=True, text=True, check=True).stdout


def test_unclosed_fence_keeps_content():
    assert "<pre><code>lost line</code></pre>" in render("before\n```\nlost line\n")


def test_quote_in_url_stays_inside_href():
    out = render('[x](https://a.com/"onclick="x)\n')
    assert 'href="https://a.com/&quot;onclick=&quot;x"' in out
    assert ' onclick=' not in out
