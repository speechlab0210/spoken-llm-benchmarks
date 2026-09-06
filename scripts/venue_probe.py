#!/usr/bin/env python3
"""One paper's venue evidence, for the daily pass.

    python scripts/venue_probe.py 2410.17196
    python scripts/venue_probe.py voicebench

Prints what the machines say (arXiv comment / journal-ref / doi, Semantic Scholar, OpenAlex, DBLP).
None of it is proof: Semantic Scholar and OpenAlex name venues before proceedings exist and get
edition years wrong, and DBLP's "CoRR" is the preprint. Take the strongest lead, open the venue's
OWN page, and record that URL in data/venues.json.
"""
import json, os, re, sys, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {'User-Agent': 'spoken-llm-benchmark-atlas/1.0 (+speechlab0210@gmail.com)'}
ATOM = '{http://www.w3.org/2005/Atom}'
ARX = '{http://arxiv.org/schemas/atom}'


def get(url, data=None, ctype=None):
    h = dict(UA)
    if ctype:
        h['Content-Type'] = ctype
    req = urllib.request.Request(url, data=data, headers=h, method='POST' if data else 'GET')
    return urllib.request.urlopen(req, timeout=60).read().decode('utf-8', 'replace')


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    arg = sys.argv[1]
    entries = json.load(open(os.path.join(ROOT, 'data', 'benchmarks.json'), encoding='utf-8'))['entries']
    hit = next((b for b in entries if b['id'] == arg or b.get('arxiv_id') == arg), None)
    aid = (hit or {}).get('arxiv_id') or arg
    title = (hit or {}).get('full_title') or (hit or {}).get('name') or ''
    print('=== %s  (arXiv:%s) ===' % (hit['id'] if hit else arg, aid))
    if title:
        print('title: %s' % title)

    import xml.etree.ElementTree as ET
    try:
        e = ET.fromstring(get('http://export.arxiv.org/api/query?id_list=%s' % aid)).find(ATOM + 'entry')
        t = ' '.join((e.findtext(ATOM + 'title') or '').split())
        print('\n[arXiv]')
        print('  title      : %s' % t)
        print('  comment    : %s' % (' '.join((e.findtext(ARX + 'comment') or '').split()) or '-'))
        print('  journal_ref: %s' % (' '.join((e.findtext(ARX + 'journal_ref') or '').split()) or '-'))
        print('  doi        : %s' % (e.findtext(ARX + 'doi') or '-'))
        print('  abs page   : https://arxiv.org/abs/%s' % aid)
        title = title or t
    except Exception as ex:
        print('\n[arXiv] ERROR %s' % ex)

    try:
        r = json.loads(get('https://api.semanticscholar.org/graph/v1/paper/batch?fields='
                           'title,venue,year,publicationVenue,publicationTypes,externalIds',
                           data=json.dumps({'ids': ['arXiv:' + aid]}).encode(), ctype='application/json'))
        p = (r or [None])[0] or {}
        print('\n[Semantic Scholar]  (a lead, never proof)')
        print('  venue: %s  year: %s  types: %s' % (p.get('venue') or '-', p.get('year'), p.get('publicationTypes')))
    except Exception as ex:
        print('\n[Semantic Scholar] ERROR %s' % ex)

    try:
        q = urllib.parse.quote(re.sub(r'[^A-Za-z0-9 :\-]+', ' ', title)[:250])
        j = json.loads(get('https://api.openalex.org/works?filter=title.search:%s&per-page=5'
                           '&select=display_name,type,publication_year,doi,primary_location'
                           '&mailto=speechlab0210@gmail.com' % q))
        print('\n[OpenAlex]  (a lead, never proof)')
        for w in j.get('results', []):
            src = ((w.get('primary_location') or {}).get('source') or {}).get('display_name')
            print('  %s | %s | %s | %s' % ((w.get('display_name') or '')[:52], w.get('type'),
                                           w.get('publication_year'), src))
    except Exception as ex:
        print('\n[OpenAlex] ERROR %s' % ex)

    try:
        q = urllib.parse.quote(re.sub(r'[^A-Za-z0-9 ]+', ' ', title)[:180])
        j = json.loads(get('https://dblp.org/search/publ/api?q=%s&format=json&h=8' % q))
        hits = j.get('result', {}).get('hits', {}).get('hit', [])
        if isinstance(hits, dict):
            hits = [hits]
        print('\n[DBLP]  ("CoRR" means the arXiv preprint, not a publication)')
        for h in hits:
            i = h.get('info', {})
            print('  %s | %s %s | %s' % ((i.get('title') or '')[:52], i.get('venue'), i.get('year'), i.get('ee')))
    except Exception as ex:
        print('\n[DBLP] ERROR %s  (this machine is often rate-limited; use https://dblp.org/search?q=... in a browser)' % ex)

    print('\nNext: open the venue\'s own page (ACL Anthology / ISCA Archive / OpenReview / publisher DOI),')
    print('quote it, and add the record to data/venues.json. No link, no claim.')


main()
