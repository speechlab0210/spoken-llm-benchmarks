#!/usr/bin/env python3
"""Settle the "same authors, different title" candidates, mechanically.

resolve_venues.py never accepts a weak match. This asks the one question that separates a
retitled paper from the group's next paper: does the candidate record actually name this
benchmark? A camera-ready that renames "AV-Odyssey Bench: Can Your Multimodal LLMs Really
Understand Audio-Visual Information?" still calls the benchmark AV-Odyssey in its abstract;
an unrelated paper by the same authors does not.

Only a benchmark name distinctive enough to be evidence is used - a name that is an ordinary
English word, or that appears in the paper's own arXiv abstract for unrelated reasons, proves
nothing and the candidate is left unresolved for a human.

Writes raw/venue/adjudicated/weak.json (accepted matches) and prints the rejects.
"""
import json, os, re, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

V = os.path.join(ROOT, 'raw', 'venue')
OUTDIR = os.path.join(V, 'adjudicated')
UA = {'User-Agent': 'spoken-llm-benchmark-atlas/1.0 (+speechlab0210@gmail.com)'}
CACHE = os.path.join(V, 'linkcache.json')

# names too generic to be evidence of anything
GENERIC = set('bench benchmark eval evaluation test suite audio speech voice sound music model '
              'models data dataset corpus task tasks core hear sonar oasis atlas amuse debate '
              'mae compa echo probe'.split())


def fetch(url, cache):
    if url in cache:
        return cache[url]
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45)
        body = r.read(400000).decode('utf-8', 'replace')
        res = {'code': r.status, 'text': re.sub(r'<[^>]+>', ' ', body)[:200000]}
    except Exception as e:
        res = {'code': str(e)[:70], 'text': ''}
    cache[url] = res
    time.sleep(0.4)
    return res


def distinctive(name):
    n = (name or '').strip()
    if len(n) < 4:
        return False
    return re.sub(r'[^a-z]', '', n.lower()) not in GENERIC


def main():
    auto = json.load(open(os.path.join(V, 'auto.json'), encoding='utf-8'))
    bench = {b['id']: b for b in json.load(open(os.path.join(ROOT, 'data', 'benchmarks.json'),
                                               encoding='utf-8'))['entries']}
    cache = json.load(open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}
    accepted, rejected, skipped = [], [], []

    for r in auto:
        cands = r.get('weak_candidates') or []
        if not cands:
            continue
        b = bench.get(r['id'], {})
        names = [b.get('name')] + list(b.get('aka') or [])
        names = [n for n in names if distinctive(n)]
        if not names:
            skipped.append((r['id'], 'no distinctive benchmark name to look for'))
            continue
        hit = None
        for c in cands:
            if not c.get('url'):
                continue
            page = fetch(c['url'], cache)
            if page['code'] != 200:
                continue
            hay = page['text'].lower()
            for n in names:
                pat = re.escape(n.lower()).replace(r'\-', '[- ]?')
                if re.search(r'(?<![a-z0-9])' + pat + r'(?![a-z0-9])', hay):
                    quote = ' '.join(page['text'].split())
                    m = re.search(r'.{0,90}' + pat + r'.{0,90}', quote, re.I)
                    hit = (c, n, m.group(0) if m else n)
                    break
            if hit:
                break
        if hit:
            c, n, quote = hit
            accepted.append({'id': r['id'], 'candidate': c, 'matched_name': n, 'quote': quote})
        else:
            rejected.append((r['id'], b.get('name'), [c.get('title') for c in cands][:2]))

    os.makedirs(OUTDIR, exist_ok=True)
    json.dump(cache, open(CACHE, 'w', encoding='utf-8'))
    # Accumulate. Once a weak candidate is confirmed, resolve_venues.py promotes it and the
    # candidate stops appearing in auto.json - so a fresh overwrite here would silently forget
    # every decision already made.
    wa = os.path.join(V, 'weak_accepted.json')
    prev = json.load(open(wa, encoding='utf-8')) if os.path.exists(wa) else []
    merged = {a['id']: a for a in prev}
    for a in accepted:
        merged[a['id']] = a
    accepted_out = sorted(merged.values(), key=lambda a: a['id'])
    json.dump(accepted_out, open(wa, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('weak_accepted.json now holds %d confirmed retitles (%d new this run)'
          % (len(accepted_out), len(accepted)))
    print('%d weak candidate sets: %d confirmed as this paper retitled, %d rejected, %d unresolvable'
          % (len(accepted) + len(rejected) + len(skipped), len(accepted), len(rejected), len(skipped)))
    for a in accepted:
        print('  KEEP  %-30s -> %s' % (a['id'], (a['candidate'].get('venue') or a['candidate'].get('title'))[:70]))
    for rid, nm, titles in rejected[:40]:
        print('  DROP  %-30s (%s) not named in: %s' % (rid, nm, '; '.join(t[:45] for t in titles if t)))
    for rid, why in skipped:
        print('  SKIP  %-30s %s' % (rid, why))


main()
