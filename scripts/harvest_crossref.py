#!/usr/bin/env python3
"""Crossref, per paper: the registered publication record behind a DOI.

Covers what the Anthology and the ISCA Archive do not — IEEE (ICASSP, SLT, ASRU, ICME, S&P),
ACM (MM, KDD), Springer, MIT Press, AAAI, PMLR. A Crossref record for a non-arXiv DOI is the
publisher's own registration, so it settles "published" the way a proceedings page does.

Writes raw/venue/crossref.json. Resumable.
"""
import json, os, re, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from titlematch import match

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(ROOT, 'raw', 'venue')
OUT = os.path.join(V, 'crossref.json')
MAIL = 'speechlab0210@gmail.com'
UA = {'User-Agent': 'spoken-llm-benchmark-atlas/1.0 (mailto:%s)' % MAIL}


def norm(t):
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', (t or '').lower()).split())


def get(url, tries=4):
    last = None
    for i in range(tries):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read())
        except Exception as e:
            last = e
            time.sleep(3 * (i + 1))
    raise last


def main():
    bench = json.load(open(os.path.join(ROOT, 'data', 'benchmarks.json'), encoding='utf-8'))['entries']
    try:
        AX = json.load(open(os.path.join(V, 'arxiv.json'), encoding='utf-8'))
    except FileNotFoundError:
        AX = {}
    out = {}
    if os.path.exists(OUT):
        out = json.load(open(OUT, encoding='utf-8'))
        print('resuming: %d done' % len(out), flush=True)

    todo = [b for b in bench if b['id'] not in out]
    for n, b in enumerate(todo, 1):
        ax = AX.get(b.get('arxiv_id') or '', {})
        title = ax.get('arxiv_title') or b.get('full_title') or b.get('name')
        cat_authors = ax.get('authors') or []
        rec = []
        try:
            j = get('https://api.crossref.org/works?query.bibliographic=%s&rows=6&mailto=%s'
                    % (urllib.parse.quote(re.sub(r'[^A-Za-z0-9 :\-]+', ' ', title)[:250]), MAIL))
            for it in j.get('message', {}).get('items', []):
                t = (it.get('title') or [''])[0]
                ra = ['%s %s' % (a.get('given', ''), a.get('family', '')) for a in (it.get('author') or [])]
                kind, score = match(title, cat_authors, t, ra)
                if not kind:
                    continue
                doi = (it.get('DOI') or '')
                if doi.startswith('10.48550'):      # the arXiv DOI is the preprint, not a publication
                    continue
                ev = it.get('event') or {}
                rec.append({
                    '_match': kind, '_score': round(score, 2), 'authors': ra,
                    'title': t, 'doi': doi, 'type': it.get('type'),
                    'container': (it.get('container-title') or [None])[0],
                    'short_container': (it.get('short-container-title') or [None])[0],
                    'event': ev.get('name'), 'event_location': ev.get('location'),
                    'event_start': ((ev.get('start') or {}).get('date-parts') or [[None]])[0],
                    'publisher': it.get('publisher'), 'page': it.get('page'), 'volume': it.get('volume'),
                    'issued': ((it.get('issued') or {}).get('date-parts') or [[None]])[0],
                    'published_print': ((it.get('published-print') or {}).get('date-parts') or [[None]])[0],
                    'url': it.get('URL') or ('https://doi.org/' + doi if doi else None),
                })
        except Exception as e:
            rec = []
            print('CR WARN %s: %s' % (b['id'], str(e)[:60]), flush=True)
        out[b['id']] = rec
        if n % 20 == 0 or n == len(todo):
            json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            print('crossref %d/%d (%s)' % (n, len(todo), b['id']), flush=True)
        time.sleep(0.5)

    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    hits = sum(1 for v in out.values() if v)
    print('WROTE %s  %d/%d catalogue entries have a non-arXiv Crossref record' % (OUT, hits, len(out)))


main()
