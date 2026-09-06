#!/usr/bin/env python3
"""OpenReview, per paper: the venue string and decision for ICLR / NeurIPS / ICML / TMLR / COLM
and their workshops.

OpenReview's own `content.venue` ("ICLR 2025 Spotlight", "NeurIPS 2025 Datasets and Benchmarks
Track") is the conference's record, so a match here settles both the venue and the track. Notes
whose invitation is DBLP.org are DBLP mirror records, not OpenReview submissions, and are marked
as such rather than mixed in.

One file per benchmark under raw/venue/openreview/, so the run is fully resumable, then merged
into raw/venue/openreview.json.

    python scripts/harvest_openreview.py [workers] [sleep]
"""
import json, os, queue, re, sys, threading, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from titlematch import match

V = os.path.join(ROOT, 'raw', 'venue')
D = os.path.join(V, 'openreview')
OUT = os.path.join(V, 'openreview.json')
UA = {'User-Agent': 'spoken-llm-benchmark-atlas/1.0 (+speechlab0210@gmail.com)'}
WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 4
SLEEP = float(sys.argv[2]) if len(sys.argv) > 2 else 0.8
LOCK = threading.Lock()
DONE = [0]


def val(c, k):
    v = c.get(k)
    if isinstance(v, dict):
        v = v.get('value')
    return v


def as_text(v):
    return v if isinstance(v, str) else ('' if v is None else str(v))


def as_names(v):
    if isinstance(v, list):
        return [x for x in v if isinstance(x, str)]
    return []


def get(url, tries=4):
    last = None
    for i in range(tries):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read())
        except Exception as e:
            last = e
            time.sleep(2 * (i + 1))
    raise last


def work(q, total, AX):
    while True:
        try:
            b = q.get_nowait()
        except queue.Empty:
            return
        ax = AX.get(b.get('arxiv_id') or '', {})
        title = ax.get('arxiv_title') or b.get('full_title') or b.get('name') or ''
        cat_authors = ax.get('authors') or []
        rec = []
        err = None
        try:
            j = get('https://api2.openreview.net/notes/search?query=%s&limit=10&content=all&group=all&source=forum'
                    % urllib.parse.quote(title[:250]))
            for note in j.get('notes', []):
                c = note.get('content', {}) or {}
                t = as_text(val(c, 'title'))
                ra = as_names(val(c, 'authors'))
                kind, score = match(title, cat_authors, t, ra)
                if not kind:
                    continue
                inv = [i for i in (note.get('invitations') or []) if isinstance(i, str)]
                rec.append({
                    '_match': kind, '_score': round(score, 2), 'authors': ra, 'title': t,
                    'venue': as_text(val(c, 'venue')), 'venueid': as_text(val(c, 'venueid')),
                    'invitations': inv,
                    'is_dblp_mirror': any(i.startswith('DBLP.org') for i in inv),
                    'forum': note.get('forum'),
                    'url': ('https://openreview.net/forum?id=%s' % note['forum']) if note.get('forum') else None,
                    'pdate': note.get('pdate'), 'cdate': note.get('cdate'),
                })
        except Exception as e:
            err = str(e)[:80]
        out = {'id': b['id'], 'hits': rec}
        if err:
            out['error'] = err
        json.dump(out, open(os.path.join(D, b['id'].replace('/', '_') + '.json'), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        with LOCK:
            DONE[0] += 1
            if DONE[0] % 20 == 0:
                print('openreview %d/%d' % (DONE[0], total), flush=True)
        time.sleep(SLEEP)


def main():
    os.makedirs(D, exist_ok=True)
    bench = json.load(open(os.path.join(ROOT, 'data', 'benchmarks.json'), encoding='utf-8'))['entries']
    AX = json.load(open(os.path.join(V, 'arxiv.json'), encoding='utf-8'))
    todo = [b for b in bench if not os.path.exists(os.path.join(D, b['id'].replace('/', '_') + '.json'))]
    print('todo %d (have %d)' % (len(todo), len(bench) - len(todo)), flush=True)
    q = queue.Queue()
    for b in todo:
        q.put(b)
    ts = []
    for _ in range(WORKERS):
        t = threading.Thread(target=work, args=(q, len(todo), AX), daemon=True)
        t.start()
        ts.append(t)
        time.sleep(0.4)
    for t in ts:
        t.join()

    merged, errs = {}, 0
    for b in bench:
        p = os.path.join(D, b['id'].replace('/', '_') + '.json')
        if os.path.exists(p):
            r = json.load(open(p, encoding='utf-8'))
            merged[b['id']] = r.get('hits', [])
            errs += 1 if r.get('error') else 0
    json.dump(merged, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    real = sum(1 for v in merged.values() if any(not x['is_dblp_mirror'] and x.get('venue') for x in v))
    print('WROTE %s  %d/%d with an OpenReview submission record (%d errors)'
          % (OUT, real, len(merged), errs), flush=True)


main()
