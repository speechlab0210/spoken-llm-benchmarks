#!/usr/bin/env python3
"""Mechanical audit of data/venues.json — the checks a language model is worst at.

Deliberately uses evidence the resolution pass did NOT rely on: the arXiv journal-ref/comment
fields and the DBLP harvest, plus arithmetic and link liveness. Prints findings; changes nothing.

    python scripts/audit_venues.py            # everything except the network link check
    python scripts/audit_venues.py --links    # also open every evidence URL
"""
import json, os, re, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(ROOT, 'raw', 'venue')
UA = {'User-Agent': 'spoken-llm-benchmark-atlas/1.0 (+speechlab0210@gmail.com)'}
FINDINGS_OK = {'acl', 'emnlp', 'naacl', 'eacl', 'aacl'}
AS_OF_YEAR = None

out = []


def flag(sev, bid, msg):
    out.append((sev, bid, msg))


def main():
    global AS_OF_YEAR
    venues = json.load(open(os.path.join(ROOT, 'data', 'venues.json'), encoding='utf-8'))
    bench = {b['id']: b for b in json.load(open(os.path.join(ROOT, 'data', 'benchmarks.json'), encoding='utf-8'))['entries']}
    recs = venues['benchmarks']
    reg = {v['id']: v for v in venues['venues']}
    AS_OF_YEAR = int(str(venues.get('as_of') or '2026')[:4])
    try:
        AX = json.load(open(os.path.join(V, 'arxiv.json'), encoding='utf-8'))
    except FileNotFoundError:
        AX = {}
    DB = {}
    dd = os.path.join(V, 'dblp')
    if os.path.isdir(dd):
        for f in os.listdir(dd):
            r = json.load(open(os.path.join(dd, f), encoding='utf-8'))
            DB[r['id']] = r.get('hits', [])

    ACC = re.compile(r'\b(accepted|camera[- ]ready|to appear|published (in|at)|proceedings of)\b', re.I)
    SUBM = re.compile(r'\b(submitted to|under review|in submission)\b', re.I)

    for bid, r in sorted(recs.items()):
        b = bench.get(bid, {})
        st = r['status']
        yr = int(r['year']) if (r.get('year') or '').isdigit() else None
        ax = AX.get(b.get('arxiv_id') or '', {})
        comment = ax.get('comment') or ''
        jref = ax.get('journal_ref') or ''
        axyear = int((b.get('arxiv_date') or '0000')[:4]) or None

        # 1. the completeness check that matters: called a preprint, but the authors say otherwise
        if st == 'preprint':
            if jref:
                flag('HIGH', bid, 'marked preprint but arXiv has a journal_ref: %r' % jref[:110])
            elif ACC.search(comment) and not SUBM.search(comment):
                flag('HIGH', bid, 'marked preprint but the arXiv comment claims acceptance: %r' % comment[:110])
            else:
                pub = [h for h in DB.get(bid, []) if (h.get('venue') or '') != 'CoRR' and h.get('title_exact')]
                if pub:
                    flag('HIGH', bid, 'marked preprint but DBLP has a non-CoRR record: %s' %
                         '; '.join('%s %s' % (h.get('venue'), h.get('year')) for h in pub[:3]))

        if st not in ('published', 'accepted'):
            continue

        # 2. a claim shown as fact must open
        url = r.get('evidence_url') or r.get('check_url')
        if r.get('publishable') and not re.match(r'^https?://', url or ''):
            flag('HIGH', bid, 'counted as %s with no usable evidence URL' % st)

        # 3. arithmetic the model cannot be trusted with
        if yr and axyear and yr < axyear:
            # a paper posted to arXiv after its own conference is common; two years apart is not
            flag('HIGH' if axyear - yr > 1 else 'MED', bid,
                 'venue year %d is before the first arXiv posting %d (%s)' % (yr, axyear, r.get('display')))
        if yr and yr > AS_OF_YEAR:
            flag('MED', bid, 'venue year %d is in the future relative to as_of %d (%s)' % (yr, AS_OF_YEAR, r.get('display')))
        if st == 'published' and yr == AS_OF_YEAR and r.get('kind') == 'conference':
            pass  # plausible; the second read is what settles whether the meeting has happened

        # 4. track sanity — "Findings" exists only in the ACL family
        tr = (r.get('track') or '').lower()
        shown = (r.get('display') or '').lower()
        if ('findings' in tr or 'findings' in shown) and r.get('venue') not in FINDINGS_OK:
            flag('MED', bid, 'a Findings track outside the ACL family (%s) - unusual, check the source: %r'
                 % (r.get('venue') or '?', r.get('display')))

        # 5. disagreement with a source the resolver did not have to use
        if jref:
            jl = jref.lower()
            nm = (reg.get(r.get('venue'), {}).get('name') or '').lower()
            full = (reg.get(r.get('venue'), {}).get('full') or '').lower()
            # compare on the venue's own words, not on the short name: a journal-ref spells out
            # "34th ACM International Conference on Multimedia (MM '26)" where the site says "ACM MM"
            toks = [w for w in re.split(r'[^a-z]+', full) if len(w) > 4]
            hit = (nm and nm in jl) or (r.get('venue') or '') in jl.replace(' ', '') or \
                  (toks and sum(1 for w in toks if w in jl) >= max(2, len(toks) // 2))
            if not hit:
                flag('MED', bid, 'venue %r disagrees with the arXiv journal_ref %r' % (r.get('display'), jref[:110]))
            m = re.search(r'\b(20\d{2})\b', jref)
            if m and yr and int(m.group(1)) != yr:
                flag('MED', bid, 'year %d disagrees with the journal_ref year %s (%r)' % (yr, m.group(1), jref[:90]))
        pub = [h for h in DB.get(bid, []) if (h.get('venue') or '') != 'CoRR' and h.get('title_exact')]
        if pub and yr:
            years = {h.get('year') for h in pub}
            if str(yr) not in years:
                flag('MED', bid, 'year %d not among the DBLP years %s for %s' % (yr, sorted(years), r.get('display')))

        # 6. registry hygiene
        v = reg.get(r.get('venue'))
        if v and v.get('unregistered'):
            flag('LOW', bid, 'venue %r is not in the curated registry — check its name/kind/community' % v['id'])
        if r.get('kind') and v and r['kind'] != v['kind'] and not v.get('unregistered'):
            flag('LOW', bid, 'record kind %r differs from the registry kind %r for %s' % (r['kind'], v['kind'], v['id']))

    # 7. near-duplicate display strings (same venue+year printed two ways)
    seen = {}
    for bid, r in recs.items():
        d = (r.get('display') or '').strip()
        if not d:
            continue
        k = re.sub(r'[^a-z0-9]', '', d.lower())
        seen.setdefault(k, set()).add(d)
    for k, forms in seen.items():
        if len(forms) > 1:
            flag('LOW', '-', 'the same venue is printed several ways: %s' % ' | '.join(sorted(forms)))

    # 8. optional link liveness
    if '--links' in sys.argv:
        urls = {}
        for bid, r in recs.items():
            u = r.get('evidence_url') or r.get('check_url')
            if r['status'] in ('published', 'accepted') and u and re.match(r'^https?://', u):
                urls.setdefault(u, []).append(bid)
        print('checking %d distinct evidence URLs ...' % len(urls), file=sys.stderr)
        for i, (u, ids) in enumerate(sorted(urls.items()), 1):
            code = None
            try:
                req = urllib.request.Request(u, headers=UA, method='GET')
                code = urllib.request.urlopen(req, timeout=45).status
            except Exception as e:
                code = str(e)[:60]
            if code != 200:
                flag('HIGH', ','.join(ids[:3]), 'evidence URL does not open (%s): %s' % (code, u))
            if i % 25 == 0:
                print('  %d/%d' % (i, len(urls)), file=sys.stderr)
            time.sleep(0.4)

    order = {'HIGH': 0, 'MED': 1, 'LOW': 2}
    out.sort(key=lambda x: (order[x[0]], x[1]))
    for sev, bid, msg in out:
        print('%-4s %-42s %s' % (sev, bid, msg))
    counts = {}
    for sev, _, _ in out:
        counts[sev] = counts.get(sev, 0) + 1
    print('\n%d findings: %s' % (len(out), counts or 'none'))


main()
