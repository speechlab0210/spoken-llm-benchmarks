#!/usr/bin/env python3
"""ACL Anthology, offline and complete: the whole bibliography, matched against the catalogue.

Downloads anthology.bib.gz once into raw/venue/, indexes it by normalised title, and writes
raw/venue/anthology.json with a record per catalogue entry. Authoritative for the ACL family
(ACL, EMNLP, NAACL, EACL, AACL, COLING, LREC, CoNLL, TACL, CL, Findings and their workshops):
a hit here IS the venue's own record, not a lead.
"""
import gzip, io, json, os, re, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from titlematch import match, split_bib_authors, tokens, fullnames
RANK = {'exact': 3, 'fuzzy': 2, 'weak': 1}


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(ROOT, 'raw', 'venue')
GZ = os.path.join(V, 'anthology.bib.gz')
OUT = os.path.join(V, 'anthology.json')
UA = {'User-Agent': 'spoken-llm-benchmark-atlas/1.0 (+speechlab0210@gmail.com)'}
FIELD = re.compile(r'^\s*(title|booktitle|journal|year|url|doi|publisher|address|month|pages|volume|author)\s*=\s*[{"](.*)$',
                   re.I)


def norm(t):
    t = re.sub(r'\{|\}|\\', '', t or '')
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', t.lower()).split())


def fetch():
    if os.path.exists(GZ) and os.path.getsize(GZ) > 1_000_000:
        print('using cached %s (%.1f MB)' % (GZ, os.path.getsize(GZ) / 1e6))
        return
    print('downloading anthology.bib.gz ...', flush=True)
    data = urllib.request.urlopen(
        urllib.request.Request('https://aclanthology.org/anthology.bib.gz', headers=UA), timeout=300).read()
    open(GZ, 'wb').write(data)
    print('  %.1f MB' % (len(data) / 1e6))


def parse():
    """Light bib parser: good enough for flat, machine-generated Anthology entries."""
    entries, cur, key, kind = [], None, None, None
    with gzip.open(GZ, 'rt', encoding='utf-8', errors='replace') as f:
        for line in f:
            m = re.match(r'\s*@(\w+)\{([^,]+),', line)
            if m:
                if cur:
                    entries.append(cur)
                kind, key = m.group(1).lower(), m.group(2).strip()
                cur = {'_key': key, '_type': kind}
                continue
            if cur is None:
                continue
            if line.strip() in ('}', '},'):
                entries.append(cur)
                cur = None
                continue
            fm = FIELD.match(line)
            if fm:
                name, val = fm.group(1).lower(), fm.group(2)
                closed = bool(re.search(r'["}],?\s*$', val))
                val = re.sub(r'[}"],?\s*$', '', val).strip()
                cur[name] = re.sub(r'[{}\\]', '', val)
                # author and editor lists wrap over several lines and only the last one is
                # closed; keep reading into the same field until it is.
                cur['_open'] = None if closed else name
                continue
            if cur.get('_open'):
                f = cur['_open']
                closed = bool(re.search(r'["}],?\s*$', line))
                cur[f] = (cur.get(f, '') + ' ' + re.sub(r'[{}\\]|["}],?\s*$', '', line).strip()).strip()
                if closed:
                    cur['_open'] = None
    if cur:
        entries.append(cur)
    return entries


def main():
    fetch()
    entries = parse()
    print('parsed %d bib entries' % len(entries))
    idx, by_surname = {}, {}
    for e in entries:
        if e['_type'] == 'proceedings' or not e.get('title'):
            continue
        idx.setdefault(norm(e['title']), []).append(e)
        e['_authors'] = split_bib_authors(e.get('author'))
        for fn in fullnames(e['_authors']):
            by_surname.setdefault(fn, []).append(e)
    print('indexed %d distinct paper titles, %d distinct author names' % (len(idx), len(by_surname)))

    bench = json.load(open(os.path.join(ROOT, 'data', 'benchmarks.json'), encoding='utf-8'))['entries']
    try:
        AX = json.load(open(os.path.join(V, 'arxiv.json'), encoding='utf-8'))
    except FileNotFoundError:
        AX = {}
    out, hits, exact_hits = {}, 0, 0
    for b in bench:
        ax = AX.get(b.get('arxiv_id') or '', {})
        # never the short benchmark name: "EMIS" exactly matches unrelated papers
        titles = [t for t in [ax.get('arxiv_title'), b.get('full_title')]
                  if t and len(t.split()) >= 4]
        if not titles:
            out[b['id']] = []
            continue
        cat_authors = ax.get('authors') or []
        fuzzy_score = None
        match_kind = 'exact'
        found = []
        for t in titles:
            k = norm(t)
            if k and k in idx:
                found = idx[k]
                break
        exact = bool(found)
        if not found:
            # camera-ready retitling: search only the papers that share an author surname with
            # this one, then require both author overlap and topical overlap.
            cands, seen_keys = [], set()
            for fn in fullnames(cat_authors):
                for e in by_surname.get(fn, []):
                    if e['_key'] not in seen_keys:
                        seen_keys.add(e['_key'])
                        cands.append(e)
            best, best_rank, best_score = None, 0, 0.0
            for e in cands:
                kind, score = match(titles[0], cat_authors, e.get('title'), e.get('_authors'))
                r = RANK.get(kind or '', 0)
                if r and (r, score) > (best_rank, best_score):
                    best, best_rank, best_score = e, r, score
            if best:
                found = [best]
                fuzzy_score = round(best_score, 2)
                match_kind = {3: 'exact', 2: 'fuzzy', 1: 'weak'}[best_rank]
        if found:
            hits += 1
            if exact:
                exact_hits += 1
        out[b['id']] = [{
            '_match': 'exact' if exact else match_kind, '_score': 1.0 if exact else fuzzy_score,
            'anthology_id': e['_key'], 'type': e['_type'], 'title': e.get('title'),
            'booktitle': e.get('booktitle'), 'journal': e.get('journal'), 'year': e.get('year'),
            'month': e.get('month'), 'pages': e.get('pages'), 'volume': e.get('volume'),
            'publisher': e.get('publisher'), 'address': e.get('address'),
            'authors': e.get('_authors'),
            'url': e.get('url') or ('https://aclanthology.org/%s/' % e['_key']), 'doi': e.get('doi'),
        } for e in found]
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('WROTE %s  %d/%d catalogue entries found in the Anthology (%d exact title, %d retitled/fuzzy)'
          % (OUT, hits, len(bench), exact_hits, hits - exact_hits))


main()
