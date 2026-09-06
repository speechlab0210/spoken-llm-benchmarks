#!/usr/bin/env python3
"""DBLP title lookup, one file per benchmark so it is fully resumable.

usage: harvest_dblp.py [workers] [sleep_seconds]   (default 1 worker, 2.5s - DBLP blocks bursts)
"""
import json, os, re, sys, threading, time, urllib.parse, urllib.request, queue
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, 'raw', 'venue', 'dblp'); os.makedirs(D, exist_ok=True)
UA = {'User-Agent': 'spoken-llm-benchmark-atlas/1.0 (+speechlab0210@gmail.com)'}
LOCK = threading.Lock(); DONE = [0]
WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 1
SLEEP = float(sys.argv[2]) if len(sys.argv) > 2 else 2.5

def norm(t):
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', (t or '').lower()).split())

def fetch(title, tries=6):
    q = urllib.parse.quote(re.sub(r'[^A-Za-z0-9 ]+', ' ', title or '')[:180])
    url = 'https://dblp.org/search/publ/api?q=%s&format=json&h=12' % q
    last = None
    for i in range(tries):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45).read().decode('utf-8', 'replace'))
        except Exception as e:
            last = e; time.sleep(1.5 * (i + 1))
    raise last

def work(q, total):
    while True:
        try: e = q.get_nowait()
        except queue.Empty: return
        p = os.path.join(D, e['id'].replace('/', '_') + '.json')
        title = e.get('full_title') or e.get('name')
        rec = {'id': e['id'], 'query': title}
        try:
            j = fetch(title)
            hits = j.get('result', {}).get('hits', {}).get('hit', [])
            if isinstance(hits, dict): hits = [hits]
            want = norm(title); keep = []
            for h in hits:
                i2 = h.get('info', {})
                ht = norm((i2.get('title') or '').rstrip('.'))
                if ht == want or (want and (ht.startswith(want[:60]) or want.startswith(ht[:60]))):
                    keep.append({'title': i2.get('title'), 'venue': i2.get('venue'), 'year': i2.get('year'),
                                 'type': i2.get('type'), 'doi': i2.get('doi'), 'ee': i2.get('ee'),
                                 'url': i2.get('url'), 'key': i2.get('key'), 'pages': i2.get('pages'),
                                 'volume': i2.get('volume'), 'title_exact': ht == want})
            rec['hits'] = keep; rec['raw_count'] = len(hits)
        except Exception as ex:
            rec['hits'] = []; rec['error'] = str(ex)
        json.dump(rec, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        with LOCK:
            DONE[0] += 1
            if DONE[0] % 15 == 0: print('dblp %d/%d' % (DONE[0], total), flush=True)
        time.sleep(SLEEP)

def main():
    entries = json.load(open(os.path.join(ROOT, 'data', 'benchmarks.json'), encoding='utf-8'))['entries']
    todo = [e for e in entries if not os.path.exists(os.path.join(D, e['id'].replace('/', '_') + '.json'))]
    print('todo %d (already have %d)' % (len(todo), len(entries) - len(todo)), flush=True)
    q = queue.Queue()
    for e in todo: q.put(e)
    ts = []
    for i in range(WORKERS):
        t = threading.Thread(target=work, args=(q, len(todo)), daemon=True); t.start(); ts.append(t); time.sleep(SLEEP)
    for t in ts: t.join()
    print('DONE %d files in %s' % (len(os.listdir(D)), D), flush=True)

main()
