#!/usr/bin/env python3
"""ISCA Archive, offline: every paper title in the proceedings we care about.

Pulls the year-index page of each ISCA event, extracts (title -> paper page URL), and matches
the catalogue against it. A hit here IS Interspeech's own record. A miss for a recent year is
not proof of absence: the archive publishes a conference's proceedings around the meeting, so
an accepted-but-not-yet-held edition simply has no index page.

Writes raw/venue/isca.json.
"""
import json, os, re, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from titlematch import match, fullnames
RANK = {'exact': 3, 'fuzzy': 2, 'weak': 1}


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(ROOT, 'raw', 'venue')
OUT = os.path.join(V, 'isca.json')
CACHE = os.path.join(V, 'isca_index')
UA = {'User-Agent': 'spoken-llm-benchmark-atlas/1.0 (+speechlab0210@gmail.com)'}

EVENTS = ([('interspeech_%d' % y, 'Interspeech %d' % y) for y in range(2016, 2027)] +
          [('odyssey_%d' % y, 'Odyssey %d' % y) for y in (2016, 2018, 2020, 2022, 2024, 2026)] +
          [('ssw_%d' % y, 'SSW %d' % y) for y in (2019, 2021, 2023, 2025)] +
          [('slate_%d' % y, 'SLaTE %d' % y) for y in (2019, 2021, 2023, 2025)])

LINK = re.compile(r'<a class="w3-text" href="([^"]+\.html)">\s*<p>\s*(.*?)\s*<br>(.*?)</a>', re.S)


def norm(t):
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', re.sub(r'<[^>]+>', ' ', t or '').lower()).split())


def get_index(slug):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, slug + '.html')
    if os.path.exists(p) and os.path.getsize(p) > 2000:
        return open(p, encoding='utf-8', errors='replace').read()
    url = 'https://www.isca-archive.org/%s/index.html' % slug
    try:
        h = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90).read().decode('utf-8', 'replace')
    except Exception as e:
        print('  %-20s no index (%s)' % (slug, str(e)[:40]), flush=True)
        return None
    open(p, 'w', encoding='utf-8').write(h)
    time.sleep(1.0)
    return h


def main():
    idx, by_surname = {}, {}
    for slug, label in EVENTS:
        h = get_index(slug)
        if not h:
            continue
        n = 0
        for href, title, tail in LINK.findall(h):
            k = norm(title)
            if not k:
                continue
            auth = [a.strip() for a in re.split(r',|;| and ',
                    ' '.join(re.sub(r'<[^>]+>', ' ', tail).split())) if a.strip()]
            e = {
                'event': label, 'slug': slug, 'title': ' '.join(re.sub(r'<[^>]+>', ' ', title).split()),
                'url': 'https://www.isca-archive.org/%s/%s' % (slug, href), 'authors': auth,
            }
            idx.setdefault(k, []).append(e)
            for fn in fullnames(auth):
                by_surname.setdefault(fn, []).append(e)
            n += 1
        print('  %-20s %5d papers' % (slug, n), flush=True)
    print('indexed %d distinct titles across the ISCA Archive' % len(idx))

    bench = json.load(open(os.path.join(ROOT, 'data', 'benchmarks.json'), encoding='utf-8'))['entries']
    try:
        AX = json.load(open(os.path.join(V, 'arxiv.json'), encoding='utf-8'))
    except FileNotFoundError:
        AX = {}
    out, hits = {}, 0
    for b in bench:
        ax = AX.get(b.get('arxiv_id') or '', {})
        # never the short benchmark name: "EMIS" exactly matches unrelated papers
        titles = [t for t in [ax.get('arxiv_title'), b.get('full_title')]
                  if t and len(t.split()) >= 4]
        if not titles:
            out[b['id']] = []
            continue
        cat_authors = ax.get('authors') or []
        found, kind = [], 'exact'
        for t in titles:
            k = norm(t)
            if k and k in idx:
                found = idx[k]
                break
        if not found:                       # camera-ready retitling
            cands, seen = [], set()
            for fn in fullnames(cat_authors):
                for e in by_surname.get(fn, []):
                    if e['url'] not in seen:
                        seen.add(e['url'])
                        cands.append(e)
            best, best_rank, best_score = None, 0, 0.0
            for e in cands:
                k2, sc = match(titles[0], cat_authors, e['title'], e['authors'])
                r = RANK.get(k2 or '', 0)
                if r and (r, sc) > (best_rank, best_score):
                    best, best_rank, best_score = e, r, sc
            if best:
                mk = {3: 'exact', 2: 'fuzzy', 1: 'weak'}[best_rank]
                found, kind = [dict(best, _match=mk, _score=round(best_score, 2))], mk
        if found:
            hits += 1
            if kind == 'exact':
                found = [dict(f, _match='exact', _score=1.0) for f in found]
        out[b['id']] = found
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('WROTE %s  %d/%d catalogue entries found in the ISCA Archive' % (OUT, hits, len(bench)))


main()
