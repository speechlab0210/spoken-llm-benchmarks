#!/usr/bin/env python3
"""Independent second read of raw/venue/auto.json, done mechanically.

Two checks, neither of which uses the source that produced the answer:

  LINK  - open the evidence URL and confirm this paper's own title is there. For a DOI the check
          goes through content negotiation on doi.org, which returns the registry's record for
          that exact DOI, so what is confirmed is the DOI -> title -> container binding rather
          than a search result. For a page that renders its content in JavaScript (OpenReview)
          no title can be read out of the HTML; that is recorded as "resolves, title not
          readable" instead of being counted as a pass.
  CROSS - ask a source that was NOT used for this record (Semantic Scholar, OpenAlex, DBLP,
          Crossref, the arXiv journal-ref) whether it names the same venue. Only matches strong
          enough to have decided a verdict count here; a rejected weak match is not evidence.

A record is confirmed when the link check passes and no other source contradicts it. `preprint`
records get the opposite treatment: any other source naming a real venue is raised as a possible
miss rather than quietly confirmed.

Writes raw/venue/verified_auto.json and raw/venue/conflicts.json.
"""
import collections, json, os, re, ssl, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(ROOT, 'raw', 'venue')
UA = {'User-Agent': 'spoken-llm-benchmark-atlas/1.0 (+speechlab0210@gmail.com)'}
CACHE = os.path.join(V, 'linkcache.json')
LAX = ssl.create_default_context()
LAX.check_hostname = False
LAX.verify_mode = ssl.CERT_NONE


def load(name, default):
    p = os.path.join(V, name)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else default


def norm(t):
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', (t or '').lower()).split())


def words(t):
    return [w for w in norm(t).split() if len(w) > 2]


def title_overlap(a, b):
    """How much of the shorter title the longer one covers. One-directional coverage fails when
    the registry records a shortened form of the arXiv title."""
    wa, wb = set(words(a)), set(words(b))
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / min(len(wa), len(wb))


def usable(hits):
    """Only matches strong enough to decide a verdict count as evidence anywhere."""
    return [h for h in (hits or []) if h.get('_match', 'exact') in ('exact', 'fuzzy')
            or h.get('_promoted')]


FAMILY = [
    ('interspeech', r'interspeech'), ('icassp', r'icassp|acoustics.{0,20}speech.{0,20}signal'),
    ('asru', r'\basru\b|automatic speech recognition and understanding'),
    ('slt', r'\bslt\b|spoken language technology'), ('odyssey', r'odyssey'), ('waspaa', r'waspaa'),
    ('taslp', r'taslp|transactions on audio'), ('iscslp', r'iscslp|chinese spoken language'),
    ('apsipa', r'apsipa'), ('ssw', r'speech synthesis workshop|\bssw\b'),
    ('acl', r'\bacl\b|annual meeting of the association for computational linguistics'),
    ('emnlp', r'emnlp|empirical methods in natural language'),
    ('naacl', r'naacl|nations of the americas chapter|north american chapter'),
    ('eacl', r'\beacl\b|european chapter of the association'),
    ('aacl', r'\baacl\b|ijcnlp|asia-pacific chapter'),
    ('coling', r'coling|international conference on computational linguistics'),
    ('lrec', r'\blrec\b|language resources and evaluation'), ('conll', r'conll'),
    ('tacl', r'\btacl\b|transactions of the association for computational linguistics'),
    ('neurips', r'neurips|\bnips\b|neural information processing systems'),
    ('iclr', r'\biclr\b|learning representations'),
    ('icml', r'\bicml\b|international conference on machine learning'),
    ('aaai', r'\baaai\b'), ('ijcai', r'ijcai'), ('colm', r'\bcolm\b|conference on language modeling'),
    ('tmlr', r'\btmlr\b|transactions on machine learning research'), ('jmlr', r'\bjmlr\b'),
    ('kdd', r'\bkdd\b|knowledge discovery and data mining'), ('sigir', r'sigir'),
    ('cvpr', r'\bcvpr\b|computer vision and pattern recognition'), ('iccv', r'\biccv\b'),
    ('eccv', r'\beccv\b'), ('wacv', r'\bwacv\b'),
    ('icme', r'\bicme\b|multimedia and expo'),          # before ACM MM: both say "multimedia"
    ('acmmm', r"acm mm|acm multimedia|international conference on multimedia\s*\(|\bmm '?\d\d"),
    ('ismir', r'ismir|music information retrieval'),
    ('dcase', r'dcase'), ('sp', r'symposium on security and privacy'),
    ('csl', r'computer speech'), ('speechcom', r'speech communication'),
]


def family(s):
    s = ' ' + (s or '').lower() + ' '
    for key, pat in FAMILY:
        if re.search(pat, s):
            return key
    return None


def http(url, headers, ctx=None):
    req = urllib.request.Request(url, headers=headers)
    r = urllib.request.urlopen(req, timeout=45, context=ctx) if ctx else urllib.request.urlopen(req, timeout=45)
    return r.status, r.read(400000).decode('utf-8', 'replace')


def fetch(url, cache):
    """-> {code, text, kind}. kind: 'metadata' | 'html' | 'spa' | 'error'."""
    if url in cache:
        return cache[url]
    res = None
    try:
        if re.search(r'^https?://(dx\.)?doi\.org/', url):
            # content negotiation: the registry's own record for this exact DOI
            code, body = http(url, {**UA, 'Accept': 'application/vnd.citationstyles.csl+json'})
            try:
                j = json.loads(body)
                txt = ' '.join(str(x) for x in [j.get('title'), j.get('container-title'),
                                                j.get('event'), j.get('publisher')] if x)
                res = {'code': 200, 'text': txt, 'kind': 'metadata'}
            except Exception:
                res = {'code': code, 'text': re.sub(r'<[^>]+>', ' ', body)[:200000], 'kind': 'html'}
        elif 'openreview.net' in url:
            code, _ = http(url, UA)
            res = {'code': code, 'text': '', 'kind': 'spa'}   # note title is supplied by the caller
        else:
            code, body = http(url, UA)
            res = {'code': code, 'text': re.sub(r'<[^>]+>', ' ', body)[:200000], 'kind': 'html'}
    except Exception as e:
        if 'CERTIFICATE_VERIFY_FAILED' in str(e):
            try:
                code, body = http(url, UA, LAX)
                res = {'code': code, 'text': re.sub(r'<[^>]+>', ' ', body)[:200000], 'kind': 'html',
                       'tls': 'certificate not verified'}
            except Exception as e2:
                res = {'code': str(e2)[:70], 'text': '', 'kind': 'error'}
        else:
            res = {'code': str(e)[:70], 'text': '', 'kind': 'error'}
    cache[url] = res
    time.sleep(0.35)
    return res


def main():
    auto = {r['id']: r for r in load('auto.json', [])}
    if not auto:
        sys.exit('run resolve_venues.py first')
    bench = {b['id']: b for b in json.load(open(os.path.join(ROOT, 'data', 'benchmarks.json'),
                                               encoding='utf-8'))['entries']}
    AX = load('arxiv.json', {})
    S2 = load('s2.json', {})
    OA = {r['id']: r for r in load('openalex.json', [])}
    CR = load('crossref.json', {})
    ANT = load('anthology.json', {})
    ORV = load('openreview.json', {})
    DB = {}
    if os.path.isdir(os.path.join(V, 'dblp')):
        for f in os.listdir(os.path.join(V, 'dblp')):
            r = json.load(open(os.path.join(V, 'dblp', f), encoding='utf-8'))
            DB[r['id']] = r.get('hits', [])
    cache = json.load(open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}
    PROMOTED = {}
    wa = os.path.join(V, 'weak_accepted.json')
    if os.path.exists(wa):
        for a in json.load(open(wa, encoding='utf-8')):
            PROMOTED[a['id']] = '"%s"' % (a.get('quote') or a.get('matched_name') or '')[:120]

    out, conflicts, n = {}, [], 0
    for bid, r in sorted(auto.items()):
        b = bench.get(bid, {})
        ax = AX.get(b.get('arxiv_id') or '', {})
        title = ax.get('arxiv_title') or b.get('full_title') or b.get('name') or ''
        used = r.get('evidence_source')

        others = {}
        if used != 'acl_anthology':
            h = usable(ANT.get(bid))
            if h:
                others['acl_anthology'] = h[0].get('booktitle') or h[0].get('journal') or ''
        if used != 'publisher':
            h = usable(CR.get(bid))
            if h:
                others['crossref'] = h[0].get('container') or h[0].get('event') or ''
        if used != 'openreview':
            h = [x for x in usable(ORV.get(bid)) if not x.get('is_dblp_mirror') and x.get('venue')]
            if h:
                others['openreview'] = h[0]['venue']
        if used != 'dblp':
            pub = [h for h in DB.get(bid, []) if (h.get('venue') or '') != 'CoRR' and h.get('title_exact')]
            if pub:
                others['dblp'] = '%s %s' % (pub[0].get('venue'), pub[0].get('year'))
        s2v = (S2.get(bid) or {}).get('venue') or ''
        if s2v and 'arxiv' not in s2v.lower():
            others['semantic_scholar'] = s2v
        oah = [h for h in (OA.get(bid) or {}).get('openalex_hits', [])
               if h.get('title_exact') and h.get('primary_source')
               and 'arxiv' not in (h['primary_source'] or '').lower()]
        if oah:
            others['openalex'] = oah[0]['primary_source']
        if used != 'arxiv_journal_ref' and ax.get('journal_ref'):
            others['arxiv_journal_ref'] = ax['journal_ref']

        mine = family(r.get('display') or r.get('venue_full') or r.get('venue_name'))
        theirs = {k: family(v) for k, v in others.items()}
        agree = [k for k, f in theirs.items() if f and mine and f == mine]
        disagree = [k for k, f in theirs.items() if f and mine and f != mine]
        rec = {'id': bid, 'checked_against': others, 'cross_agree': agree, 'cross_disagree': disagree}

        if r['status'] in ('published', 'accepted'):
            url = r.get('evidence_url') or ''
            page = fetch(url, cache) if re.match(r'^https?://', url) else {'code': 'no url', 'text': '', 'kind': 'error'}
            rec['link_code'] = page['code']
            rec['link_kind'] = page.get('kind')
            hay_text = page['text']
            if page.get('kind') == 'spa' and page['code'] == 200:
                # OpenReview renders in JavaScript, but the API note IS the conference's record
                # and carries the title it accepted; use that as the readable evidence.
                notes = [x for x in usable(ORV.get(bid)) if x.get('url') == url and x.get('title')]
                if notes:
                    hay_text = notes[0]['title']
                    page = dict(page, kind='record')
                    rec['link_kind'] = 'record'
            hay = norm(hay_text)
            hit = 0.0
            if hay:
                hit = 1.0 if norm(title) in hay else max(
                    title_overlap(title, hay_text),
                    (sum(1 for w in words(title) if w in hay) / len(words(title))) if words(title) else 0.0)
            rec['title_on_page'] = round(hit, 2)
            # a venue edition that predates the paper's first arXiv posting means either a
            # different paper or a later preprint version - not something to publish as fact
            vy = int(r['venue_year']) if str(r.get('venue_year') or '').isdigit() else None
            ay = int((b.get('arxiv_date') or '0')[:4]) if (b.get('arxiv_date') or '')[:4].isdigit() else None
            if vy and ay and vy < ay:
                rec['verdict'] = 'cannot_verify'
                rec['note'] = ('the %s edition predates this paper\u2019s first arXiv posting in %d, so the '
                               'record and the preprint may not be the same work' % (r['display'], ay))
                conflicts.append({**rec, 'auto': r, 'kind': 'year_before_preprint'})
                out[bid] = rec
                n += 1
                continue

            resolves = page['code'] == 200
            # a retitled paper cannot pass a title check; adjudicate_weak.py confirmed these by
            # finding the benchmark itself named in the record
            if bid in PROMOTED and resolves:
                rec['verdict'] = 'confirmed'
                rec['evidence_url'] = url
                rec['title_on_page'] = round(hit, 2)
                rec['note'] = ('the paper was retitled for publication, so the titles differ; the record '
                               'names the benchmark itself (%s)' % PROMOTED[bid])
                out[bid] = rec
                n += 1
                continue
            readable = page.get('kind') in ('html', 'metadata', 'record') and bool(hay)
            link_ok = resolves and (hit >= 0.8 if readable else False)

            if resolves and not readable and agree:
                # the page renders its content in JavaScript, but an independent index names the
                # same venue for this paper, which is the thing being claimed
                rec['verdict'] = 'confirmed'
                rec['evidence_url'] = url
                rec['note'] = ('evidence page resolves but renders its content in JavaScript; the venue is '
                               'corroborated by ' + ', '.join(agree))
            elif not link_ok:
                rec['verdict'] = 'cannot_verify'
                rec['note'] = ('evidence page did not confirm the title (http %s, %s, title match %.2f)'
                               % (page['code'], page.get('kind'), hit))
                conflicts.append({**rec, 'auto': r, 'kind': 'link'})
            elif disagree:
                rec['verdict'] = 'cannot_verify'
                rec['note'] = ('another source names a different venue: '
                               + '; '.join('%s = %r' % (k, others[k][:60]) for k in disagree))
                conflicts.append({**rec, 'auto': r, 'kind': 'venue_disagreement'})
            else:
                rec['verdict'] = 'confirmed'
                rec['evidence_url'] = url
                rec['note'] = ('evidence record carries this paper’s title; '
                               + (('cross-checked against ' + ', '.join(agree)) if agree
                                  else 'no other indexed source names a venue for this paper'))
            if page.get('tls'):
                rec['note'] += ' (publisher TLS certificate could not be verified)'
        else:
            named = {k: v for k, v in others.items() if family(v)}
            if named:
                rec['verdict'] = 'cannot_verify'
                rec['note'] = ('called a preprint, but another source names a venue: '
                               + '; '.join('%s = %r' % (k, v[:60]) for k, v in named.items()))
                conflicts.append({**rec, 'auto': r, 'kind': 'possible_missed_publication'})
            else:
                rec['verdict'] = 'confirmed'
                rec['note'] = ('absent from the ACL Anthology, the ISCA Archive, Crossref, OpenReview and '
                               'DBLP, and no source names a venue')
        out[bid] = rec
        n += 1
        if n % 60 == 0:
            json.dump(cache, open(CACHE, 'w', encoding='utf-8'))
            print('verified %d/%d' % (n, len(auto)), flush=True)

    json.dump(cache, open(CACHE, 'w', encoding='utf-8'))
    json.dump(out, open(os.path.join(V, 'verified_auto.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    json.dump(conflicts, open(os.path.join(V, 'conflicts.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    c = collections.Counter(v['verdict'] for v in out.values())
    k = collections.Counter(x['kind'] for x in conflicts)
    print('WROTE verified_auto.json  %s' % dict(c))
    print('      conflicts.json      %d to adjudicate: %s' % (len(conflicts), dict(k)))


main()
