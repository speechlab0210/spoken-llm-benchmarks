#!/usr/bin/env python3
"""Third mechanical venue source: Semantic Scholar batch lookup by arXiv id.

S2's `venue` is a lead, not proof — it sometimes names a venue before the paper is
actually in proceedings, and sometimes gets the year wrong. It is here so a claim can be
cross-checked against a source that did not produce it. Writes raw/venue/s2.json.
"""
import json, os, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'raw', 'venue', 's2.json')
H = {'User-Agent': 'spoken-llm-benchmark-atlas/1.0 (+speechlab0210@gmail.com)', 'Content-Type': 'application/json'}
URL = ('https://api.semanticscholar.org/graph/v1/paper/batch?fields='
       'title,venue,year,publicationVenue,externalIds,publicationTypes,journal,url')


def post(ids, tries=8):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(URL, data=json.dumps({'ids': ids}).encode(), headers=H, method='POST')
            return json.loads(urllib.request.urlopen(req, timeout=90).read())
        except Exception as e:
            last = e
            time.sleep(6 * (i + 1))
    raise last


def main():
    entries = json.load(open(os.path.join(ROOT, 'data', 'benchmarks.json'), encoding='utf-8'))['entries']
    pairs = [(b['id'], b['arxiv_id']) for b in entries if b.get('arxiv_id')]
    out = {}
    for i in range(0, len(pairs), 100):
        chunk = pairs[i:i + 100]
        try:
            res = post(['arXiv:' + a for _, a in chunk])
        except Exception as e:
            print('S2 WARN batch %d: %s' % (i, e), flush=True)
            continue
        for (bid, aid), p in zip(chunk, res):
            if not p:
                out[bid] = {'arxiv_id': aid, 'found': False}
                continue
            j = p.get('journal') or {}
            pv = p.get('publicationVenue') or {}
            out[bid] = {
                'arxiv_id': aid, 'found': True, 'title': p.get('title'),
                'venue': p.get('venue'), 'year': p.get('year'),
                'publication_venue_name': pv.get('name'), 'publication_venue_type': pv.get('type'),
                'publication_venue_alternates': pv.get('alternate_names'),
                'publication_types': p.get('publicationTypes'),
                'journal_name': j.get('name'), 'journal_volume': j.get('volume'), 'journal_pages': j.get('pages'),
                'external_ids': p.get('externalIds'), 'url': p.get('url'),
            }
        print('s2 %d/%d' % (min(i + 100, len(pairs)), len(pairs)), flush=True)
        time.sleep(4)
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('WROTE %s n=%d found=%d' % (OUT, len(out), sum(1 for v in out.values() if v.get('found'))), flush=True)


main()
