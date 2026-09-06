#!/usr/bin/env python3
"""OpenAlex title search (+ Crossref for any DOI): a venue candidate source, never proof.

Deliberately does NOT read DBLP: it exists so an answer can be cross-checked against a source
that was not used to produce it. Like Semantic Scholar it names venues before proceedings exist,
so verify_venues.py treats it as corroboration only. Writes raw/venue/openalex.json.
"""
import json, os, re, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'raw', 'venue', 'openalex.json')
MAIL = 'speechlab0210@gmail.com'
UA = {'User-Agent': 'spoken-llm-benchmark-atlas/1.0 (mailto:%s)' % MAIL}


def get(url, tries=4, sleep=2.0):
    last = None
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read().decode('utf-8', 'replace')
        except Exception as e:
            last = e
            if '404' in str(e):
                raise
            time.sleep(sleep * (i + 1))
    raise last


def norm(t):
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', (t or '').lower()).split())


def openalex(title):
    q = urllib.parse.quote(re.sub(r'[^A-Za-z0-9 :\-]+', ' ', title or '')[:250])
    url = ('https://api.openalex.org/works?filter=title.search:%s&per-page=8'
           '&select=id,doi,display_name,type,publication_year,primary_location,locations,best_oa_location,ids'
           '&mailto=%s' % (q, MAIL))
    j = json.loads(get(url))
    out = []
    want = norm(title)
    for w in j.get('results', []):
        wt = norm(w.get('display_name'))
        if not (wt == want or wt.startswith(want[:60]) or want.startswith(wt[:60])):
            continue
        locs = []
        for l in w.get('locations', []) or []:
            s = l.get('source') or {}
            if s.get('display_name'):
                locs.append({'source': s.get('display_name'), 'type': s.get('type'),
                             'host': (s.get('host_organization_name')), 'landing': l.get('landing_page_url'),
                             'version': l.get('version')})
        pl = (w.get('primary_location') or {}).get('source') or {}
        out.append({
            'openalex': w.get('id'), 'title': w.get('display_name'), 'type': w.get('type'),
            'year': w.get('publication_year'), 'doi': w.get('doi'),
            'primary_source': pl.get('display_name'), 'primary_source_type': pl.get('type'),
            'title_exact': wt == want, 'locations': locs,
        })
    return out


def crossref(doi):
    d = re.sub(r'^https?://(dx\.)?doi\.org/', '', doi or '')
    j = json.loads(get('https://api.crossref.org/works/' + urllib.parse.quote(d) + '?mailto=' + MAIL))
    m = j.get('message', {})
    ev = m.get('event') or {}
    return {'container': (m.get('container-title') or [None])[0], 'type': m.get('type'),
            'event': ev.get('name'), 'event_location': ev.get('location'),
            'publisher': m.get('publisher'), 'title': (m.get('title') or [None])[0],
            'issued': ((m.get('issued') or {}).get('date-parts') or [[None]])[0]}


def main():
    entries = json.load(open(os.path.join(ROOT, 'data', 'benchmarks.json'), encoding='utf-8'))['entries']
    done = {}
    if os.path.exists(OUT):
        done = {r['id']: r for r in json.load(open(OUT, encoding='utf-8'))}
        print('resuming: %d done' % len(done), flush=True)
    recs = list(done.values())
    todo = [e for e in entries if e['id'] not in done]
    for n, e in enumerate(todo, 1):
        title = e.get('full_title') or e.get('name')
        r = {'id': e['id'], 'name': e.get('name'), 'arxiv_id': e.get('arxiv_id'), 'query_title': title}
        try:
            r['openalex_hits'] = openalex(title)
        except Exception as ex:
            r['openalex_hits'] = []
            r['openalex_error'] = str(ex)
            print('OA WARN %s: %s' % (e['id'], ex), flush=True)
        # crossref only for a non-arXiv DOI found above (the arXiv DOI tells us nothing new)
        for h in r.get('openalex_hits', []):
            d = h.get('doi') or ''
            if d and '10.48550' not in d:
                try:
                    h['crossref'] = crossref(d)
                except Exception as ex:
                    h['crossref_error'] = str(ex)
                time.sleep(0.6)
        recs.append(r)
        if n % 10 == 0 or n == len(todo):
            json.dump(recs, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            print('openalex %d/%d (%s)' % (n, len(todo), e['id']), flush=True)
        time.sleep(0.35)
    json.dump(recs, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('WROTE %s n=%d' % (OUT, len(recs)), flush=True)


if __name__ == '__main__':
    main()
