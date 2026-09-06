#!/usr/bin/env python3
"""arXiv metadata for every catalogue entry: comment, journal_ref, doi, latest version."""
import json, os, re, time, urllib.request
import xml.etree.ElementTree as ET
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'raw', 'venue', 'arxiv.json')
UA = {'User-Agent': 'spoken-llm-benchmark-atlas/1.0 (+speechlab0210@gmail.com)'}
ATOM = '{http://www.w3.org/2005/Atom}'; ARX = '{http://arxiv.org/schemas/atom}'

def get(url, tries=5):
    last = None
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read().decode('utf-8', 'replace')
        except Exception as e:
            last = e; time.sleep(3 * (i + 1))
    raise last

def main():
    ids = [b['arxiv_id'] for b in json.load(open(os.path.join(ROOT, 'data', 'benchmarks.json'), encoding='utf-8'))['entries'] if b.get('arxiv_id')]
    out = {}
    for i in range(0, len(ids), 40):
        chunk = ids[i:i + 40]
        xml = get('http://export.arxiv.org/api/query?id_list=%s&max_results=%d' % (','.join(chunk), len(chunk)))
        for e in ET.fromstring(xml).findall(ATOM + 'entry'):
            aid = e.findtext(ATOM + 'id') or ''
            m = re.search(r'abs/(.+?)v(\d+)$', aid)
            bare = m.group(1) if m else aid.rsplit('/', 1)[-1]
            out[bare] = {
                'arxiv_title': ' '.join((e.findtext(ATOM + 'title') or '').split()),
                'arxiv_version': m.group(2) if m else '',
                'arxiv_updated': e.findtext(ATOM + 'updated'),
                'arxiv_published': e.findtext(ATOM + 'published'),
                'comment': ' '.join((e.findtext(ARX + 'comment') or '').split()) or None,
                'journal_ref': ' '.join((e.findtext(ARX + 'journal_ref') or '').split()) or None,
                'doi': e.findtext(ARX + 'doi'),
                'authors': [' '.join((a.findtext(ATOM + 'name') or '').split())
                            for a in e.findall(ATOM + 'author')],
            }
        print('arxiv %d/%d' % (min(i + 40, len(ids)), len(ids)), flush=True)
        time.sleep(3.2)
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('WROTE %s n=%d' % (OUT, len(out)), flush=True)

main()
