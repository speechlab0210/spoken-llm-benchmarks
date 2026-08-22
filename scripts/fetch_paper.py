# Download an arXiv paper to local text so an agent can read EXACT numbers from tables.
# Prefers the arXiv HTML rendering (tables survive); falls back to PDF text extraction.
# Usage: python scripts/fetch_paper.py 2410.17196 [2503.01234 ...]
# Output: raw/papers/<id>.txt   (prints the path + char count)

import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "raw" / "papers"
UA = {"User-Agent": "Mozilla/5.0 (compatible; spoken-llm-benchmark-atlas/1.0)"}


class Textify(HTMLParser):
    """Flatten arXiv HTML, keeping table structure as pipe-separated rows."""

    SKIP = {"script", "style", "noscript"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.buf = []
        self.skip_depth = 0
        self.in_cell = False

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip_depth += 1
        elif tag in ("td", "th"):
            self.in_cell = True
            self.buf.append(" | ")
        elif tag == "tr":
            self.buf.append("\nROW: ")
        elif tag == "table":
            self.buf.append("\n\n[TABLE]\n")
        elif tag in ("p", "div", "li", "h1", "h2", "h3", "h4", "section", "br"):
            self.buf.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip_depth:
            self.skip_depth -= 1
        elif tag in ("td", "th"):
            self.in_cell = False
        elif tag == "table":
            self.buf.append("\n[/TABLE]\n\n")

    def handle_data(self, data):
        if self.skip_depth:
            return
        t = data.replace("\xa0", " ")
        t = re.sub(r"[ \t]+", " ", t)
        if t.strip():
            self.buf.append(t if self.in_cell else t)

    def text(self):
        s = "".join(self.buf)
        s = re.sub(r"\n{3,}", "\n\n", s)
        s = re.sub(r"[ \t]{2,}", " ", s)
        return s.strip()


def get(url, timeout=90):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def from_html(aid):
    for url in (f"https://arxiv.org/html/{aid}v3", f"https://arxiv.org/html/{aid}v2",
                f"https://arxiv.org/html/{aid}v1", f"https://arxiv.org/html/{aid}",
                f"https://ar5iv.labs.arxiv.org/html/{aid}"):
        try:
            raw = get(url).decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            continue
        if len(raw) < 3000 or "No HTML for" in raw[:4000]:
            continue
        p = Textify()
        p.feed(raw)
        txt = p.text()
        if len(txt) > 4000:
            return txt, url
    return None, None


def from_pdf(aid):
    try:
        from pypdf import PdfReader
    except ImportError:
        return None, None
    tmp = OUT / f"{aid}.pdf"
    for url in (f"https://arxiv.org/pdf/{aid}", f"https://arxiv.org/pdf/{aid}v1"):
        try:
            tmp.write_bytes(get(url))
            reader = PdfReader(str(tmp))
            txt = "\n".join(p.extract_text() or "" for p in reader.pages)
            tmp.unlink(missing_ok=True)
            if len(txt) > 2000:
                return txt, url
        except Exception:  # noqa: BLE001
            tmp.unlink(missing_ok=True)
            continue
    return None, None


def main():
    ids = [a.strip() for a in sys.argv[1:] if a.strip()]
    if not ids:
        raise SystemExit("usage: fetch_paper.py <arxiv_id> [<arxiv_id> ...]")
    OUT.mkdir(parents=True, exist_ok=True)
    for aid in ids:
        aid = re.sub(r"^arxiv:", "", aid, flags=re.I).split("v")[0]
        dest = OUT / f"{aid}.txt"
        if dest.exists() and dest.stat().st_size > 4000:
            print(f"CACHED {dest}  ({dest.stat().st_size} bytes)")
            continue
        txt, src = from_html(aid)
        how = "html"
        if not txt:
            txt, src = from_pdf(aid)
            how = "pdf"
        if not txt:
            print(f"FAIL   {aid}  (no HTML, no PDF)")
            continue
        dest.write_text(f"# source: {src}  ({how})\n# arxiv: {aid}\n\n{txt}",
                        encoding="utf-8")
        print(f"OK     {dest}  ({len(txt)} chars via {how})")


if __name__ == "__main__":
    main()
