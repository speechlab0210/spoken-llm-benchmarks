#!/usr/bin/env python3
"""raw/venue/auto.json + verified_auto.json (+ adjudicated/) -> data/venues.json.

Reconciliation follows the same rule the institution pass uses: a record counts only when an
independent second read confirmed it (or corrected it). "cannot_verify" records are kept and
shown, but flagged unpublishable so they never enter a statistic.

Pipeline order:
    harvest_arxiv_meta / harvest_anthology / harvest_isca / harvest_crossref /
    harvest_openreview / harvest_dblp / harvest_s2 / harvest_openalex  (evidence)
 -> resolve_venues.py      (deterministic verdicts from that evidence)
 -> adjudicate_weak.py     (settle same-author-different-title candidates) -> resolve again
 -> verify_venues.py       (mechanical second read: link check + cross-source)
 -> build_venues.py        (this file)
 -> audit_venues.py        (arithmetic and consistency findings)
"""
import json, os, re, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(ROOT, 'raw', 'venue')
OUT = os.path.join(ROOT, 'data', 'venues.json')
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
FLAGS = {a for a in sys.argv[1:] if a.startswith('--')}
AS_OF = ARGS[0] if ARGS else None
OUT = ARGS[1] if len(ARGS) > 1 else OUT
# --assume-confirmed is a DRY-RUN switch for testing the render before the second read has run.
# It must never be used to produce the published file.
ASSUME = '--assume-confirmed' in FLAGS
if not AS_OF:
    sys.exit('usage: build_venues.py <as-of YYYY-MM-DD>   (no clock in this script - pass the date)')

# ---------------------------------------------------------------- venue registry
# id, display name, official name, kind, community, aliases the resolvers actually produce.
# "community" groups the venue by the research community that runs it - the thing worth showing,
# because this field is claimed by several communities at once.
REG = [
    ('interspeech', 'Interspeech', 'Interspeech (ISCA)', 'conference', 'speech',
     ['interspeech', 'isca interspeech', 'proceedings of interspeech', 'inter speech']),
    ('icassp', 'ICASSP', 'IEEE International Conference on Acoustics, Speech and Signal Processing',
     'conference', 'speech',
     ['icassp', 'ieee icassp', 'ieee international conference on acoustics speech and signal processing']),
    ('asru', 'ASRU', 'IEEE Automatic Speech Recognition and Understanding Workshop', 'conference', 'speech',
     ['asru', 'ieee asru', 'automatic speech recognition and understanding',
      'ieee automatic speech recognition and understanding workshop']),
    ('slt', 'SLT', 'IEEE Spoken Language Technology Workshop', 'conference', 'speech',
     ['slt', 'ieee slt', 'spoken language technology workshop', 'ieee spoken language technology workshop']),
    ('odyssey', 'Odyssey', 'The Speaker and Language Recognition Workshop (Odyssey)', 'conference', 'speech',
     ['odyssey']),
    ('waspaa', 'WASPAA', 'IEEE Workshop on Applications of Signal Processing to Audio and Acoustics',
     'conference', 'speech', ['waspaa']),
    ('iscslp', 'ISCSLP', 'International Symposium on Chinese Spoken Language Processing', 'conference', 'speech',
     ['iscslp', 'international symposium on chinese spoken language processing']),
    ('apsipa', 'APSIPA ASC', 'APSIPA Annual Summit and Conference', 'conference', 'speech',
     ['apsipa', 'apsipa asc']),
    ('ssw', 'SSW', 'ISCA Speech Synthesis Workshop', 'workshop', 'speech', ['ssw', 'speech synthesis workshop']),
    ('taslp', 'IEEE/ACM TASLP', 'IEEE/ACM Transactions on Audio, Speech and Language Processing',
     'journal', 'speech',
     ['taslp', 'ieee acm taslp', 'ieee acm transactions on audio speech and language processing',
      'ieee transactions on audio speech and language processing']),
    ('csl', 'Computer Speech & Language', 'Computer Speech & Language', 'journal', 'speech',
     ['csl', 'computer speech and language', 'computer speech & language']),
    ('speechcom', 'Speech Communication', 'Speech Communication', 'journal', 'speech', ['speech communication']),

    ('acl', 'ACL', 'Annual Meeting of the Association for Computational Linguistics', 'conference', 'nlp',
     ['acl', 'annual meeting of the association for computational linguistics', 'acl main',
      'acl main conference', 'proceedings of acl']),
    ('emnlp', 'EMNLP', 'Conference on Empirical Methods in Natural Language Processing', 'conference', 'nlp',
     ['emnlp', 'conference on empirical methods in natural language processing']),
    ('naacl', 'NAACL', 'Conference of the North American Chapter of the Association for Computational Linguistics',
     'conference', 'nlp',
     ['naacl', 'naacl hlt', 'north american chapter of the association for computational linguistics']),
    ('eacl', 'EACL', 'Conference of the European Chapter of the Association for Computational Linguistics',
     'conference', 'nlp', ['eacl', 'european chapter of the association for computational linguistics']),
    ('aacl', 'AACL-IJCNLP', 'Asia-Pacific Chapter of the Association for Computational Linguistics',
     'conference', 'nlp', ['aacl', 'aacl ijcnlp', 'ijcnlp aacl']),
    ('coling', 'COLING', 'International Conference on Computational Linguistics', 'conference', 'nlp', ['coling']),
    ('lrec', 'LREC', 'International Conference on Language Resources and Evaluation', 'conference', 'nlp',
     ['lrec', 'lrec coling', 'language resources and evaluation conference']),
    ('conll', 'CoNLL', 'Conference on Computational Natural Language Learning', 'conference', 'nlp', ['conll']),
    ('tacl', 'TACL', 'Transactions of the Association for Computational Linguistics', 'journal', 'nlp',
     ['tacl', 'transactions of the association for computational linguistics']),
    ('cl', 'Computational Linguistics', 'Computational Linguistics (MIT Press)', 'journal', 'nlp',
     ['computational linguistics']),

    ('neurips', 'NeurIPS', 'Conference on Neural Information Processing Systems', 'conference', 'ml',
     ['neurips', 'nips', 'neural information processing systems',
      'advances in neural information processing systems', 'conference on neural information processing systems']),
    ('iclr', 'ICLR', 'International Conference on Learning Representations', 'conference', 'ml',
     ['iclr', 'international conference on learning representations']),
    ('icml', 'ICML', 'International Conference on Machine Learning', 'conference', 'ml',
     ['icml', 'international conference on machine learning']),
    ('aaai', 'AAAI', 'AAAI Conference on Artificial Intelligence', 'conference', 'ml',
     ['aaai', 'aaai conference on artificial intelligence']),
    ('ijcai', 'IJCAI', 'International Joint Conference on Artificial Intelligence', 'conference', 'ml', ['ijcai']),
    ('colm', 'COLM', 'Conference on Language Modeling', 'conference', 'ml',
     ['colm', 'conference on language modeling']),
    ('tmlr', 'TMLR', 'Transactions on Machine Learning Research', 'journal', 'ml',
     ['tmlr', 'transactions on machine learning research']),
    ('jmlr', 'JMLR', 'Journal of Machine Learning Research', 'journal', 'ml', ['jmlr']),
    ('kdd', 'KDD', 'ACM SIGKDD Conference on Knowledge Discovery and Data Mining', 'conference', 'ml',
     ['kdd', 'sigkdd']),
    ('sigir', 'SIGIR', 'ACM SIGIR Conference on Research and Development in Information Retrieval',
     'conference', 'ml', ['sigir']),
    ('webconf', 'The Web Conference', 'The ACM Web Conference', 'conference', 'ml',
     ['www', 'the web conference']),

    ('cvpr', 'CVPR', 'IEEE/CVF Conference on Computer Vision and Pattern Recognition', 'conference', 'vision-mm',
     ['cvpr', 'computer vision and pattern recognition']),
    ('iccv', 'ICCV', 'IEEE/CVF International Conference on Computer Vision', 'conference', 'vision-mm', ['iccv']),
    ('eccv', 'ECCV', 'European Conference on Computer Vision', 'conference', 'vision-mm', ['eccv']),
    ('wacv', 'WACV', 'IEEE/CVF Winter Conference on Applications of Computer Vision', 'conference', 'vision-mm',
     ['wacv']),
    ('acmmm', 'ACM MM', 'ACM International Conference on Multimedia', 'conference', 'vision-mm',
     ['acm mm', 'acmmm', 'acm multimedia', 'acm international conference on multimedia']),
    ('icme', 'ICME', 'IEEE International Conference on Multimedia and Expo', 'conference', 'vision-mm',
     ['icme', 'ieee icme']),

    ('ismir', 'ISMIR', 'International Society for Music Information Retrieval Conference', 'conference',
     'audio-music', ['ismir', 'international society for music information retrieval conference']),
    ('dcase', 'DCASE', 'Workshop on Detection and Classification of Acoustic Scenes and Events', 'workshop',
     'audio-music', ['dcase']),

    ('chi', 'CHI', 'ACM CHI Conference on Human Factors in Computing Systems', 'conference', 'other',
     ['chi', 'acm chi']),
    ('ieee-sp', 'IEEE S&P', 'IEEE Symposium on Security and Privacy', 'conference', 'other',
     ['ieee sp', 'ieee s p', 'ieee s&p', 'symposium on security and privacy',
      'ieee symposium on security and privacy']),
    ('ieee-tai', 'IEEE TAI', 'IEEE Transactions on Artificial Intelligence', 'journal', 'ml',
     ['ieee tai', 'ieee transactions on artificial intelligence']),
    ('comsnets', 'COMSNETS', 'International Conference on COMmunication Systems and NETworks',
     'conference', 'other',
     ['comsnets', 'international conference on communication systems and networks']),
]
NAME2ID = {}
REGISTRY = []
for vid, name, full, kind, comm, aliases in REG:
    REGISTRY.append({'id': vid, 'name': name, 'full': full, 'kind': kind, 'community': comm})
    for a in set(aliases + [name.lower(), vid]):
        NAME2ID[' '.join(re.sub(r'[^a-z0-9&]+', ' ', a).split())] = vid


def key(s):
    return ' '.join(re.sub(r'[^a-z0-9&]+', ' ', (s or '').lower()).split())


def canon(venue_name, venue_full, kind, parent=None):
    """Map a resolver's venue string onto the registry; an unknown venue gets its own entry.

    An auto-created workshop belongs to its parent conference's community - a NeurIPS workshop
    is machine learning, not "Other"."""
    for cand in (venue_name, venue_full):
        k = key(cand)
        if not k:
            continue
        if k in NAME2ID:
            return NAME2ID[k]
        k2 = re.sub(r'\s*(19|20)\d{2}$', '', k).strip()
        if k2 and k2 in NAME2ID:
            return NAME2ID[k2]
    k = key(venue_name) or key(venue_full)
    if not k:
        return None
    k = re.sub(r'\s*(19|20)\d{2}$', '', k).strip()
    vid = re.sub(r'[^a-z0-9]+', '-', k)[:48].strip('-')
    if not vid:
        return None
    if not any(r['id'] == vid for r in REGISTRY):
        comm = 'other'
        pk = key(re.sub(r'\s*(19|20)\d{2}\s*$', '', parent or ''))
        if pk and pk in NAME2ID:
            pv = next((r for r in REGISTRY if r['id'] == NAME2ID[pk]), None)
            if pv:
                comm = pv['community']
        REGISTRY.append({'id': vid, 'name': (venue_name or venue_full or '').strip(),
                         'full': (venue_full or venue_name or '').strip(),
                         'kind': kind or 'other', 'community': comm, 'unregistered': True})
        NAME2ID[k] = vid
    return vid


def load_dir(sub):
    out = {}
    d = os.path.join(V, sub)
    if not os.path.isdir(d):
        return out
    for f in sorted(os.listdir(d)):
        if not f.endswith('.json'):
            continue
        try:
            arr = json.load(open(os.path.join(d, f), encoding='utf-8'))
        except Exception as e:
            print('SKIP %s/%s: %s' % (sub, f, e))
            continue
        if isinstance(arr, dict):
            arr = arr.get('records') or arr.get('verdicts') or []
        for r in arr:
            if isinstance(r, dict) and r.get('id'):
                out[r['id']] = r
    return out


def clean(s):
    s = (s or '').strip()
    return s or None


# Resolvers write prose into evidence_source ("ACL Anthology page 2023.tacl-1.15"), so the
# provenance bucket is derived from the URL host, which cannot be paraphrased.
HOSTS = [
    ('aclanthology.org', 'acl_anthology'),
    ('isca-archive.org', 'isca_archive'), ('isca-speech.org', 'isca_archive'),
    ('openreview.net', 'openreview'),
    ('ieeexplore.ieee.org', 'ieee'), ('ieee.org', 'ieee'),
    ('dl.acm.org', 'acm'), ('acm.org', 'acm'),
    ('dblp.org', 'dblp'), ('dblp.uni-trier.de', 'dblp'),
    ('doi.org', 'publisher'), ('crossref.org', 'publisher'),
    ('link.springer.com', 'publisher'), ('sciencedirect.com', 'publisher'),
    ('direct.mit.edu', 'publisher'), ('mitpressjournals.org', 'publisher'),
    ('proceedings.mlr.press', 'publisher'), ('mlr.press', 'publisher'),
    ('papers.nips.cc', 'publisher'), ('neurips.cc', 'publisher'),
    ('proceedings.neurips.cc', 'publisher'),
    ('ojs.aaai.org', 'publisher'), ('aaai.org', 'publisher'),
    ('ijcai.org', 'publisher'), ('ismir.net', 'publisher'),
    ('thecvf.com', 'publisher'), ('jmlr.org', 'publisher'),
    ('arxiv.org', 'arxiv'),
]


KNOWN_SOURCES = {'acl_anthology', 'isca_archive', 'openreview', 'ieee', 'acm', 'dblp',
                 'publisher', 'arxiv_comment', 'arxiv_journal_ref', 'arxiv', 'other'}


def evidence_bucket(url, text):
    # the deterministic resolver already names its source; only free-text sources (from an
    # earlier agent pass) need to be inferred from the URL host
    if (text or '').strip() in KNOWN_SOURCES:
        return text.strip()
    u = (url or '').lower()
    for host, tag in HOSTS:
        if host in u:
            if tag != 'arxiv':
                return tag
            t = (text or '').lower()
            return 'arxiv_journal_ref' if ('journal' in t or 'journal_ref' in t) else 'arxiv_comment'
    t = (text or '').lower()
    for needle, tag in [('anthology', 'acl_anthology'), ('isca', 'isca_archive'),
                        ('openreview', 'openreview'), ('journal_ref', 'arxiv_journal_ref'),
                        ('journal reference', 'arxiv_journal_ref'), ('arxiv', 'arxiv_comment'),
                        ('ieee', 'ieee'), ('acm', 'acm'), ('dblp', 'dblp'),
                        ('crossref', 'publisher'), ('doi', 'publisher'), ('proceedings', 'publisher')]:
        if needle in t:
            return tag
    return 'other'



def main():
    bench = json.load(open(os.path.join(ROOT, 'data', 'benchmarks.json'), encoding='utf-8'))['entries']
    valid = {b['id'] for b in bench}
    # deterministic resolution + its mechanical second read, then any human/agent adjudication
    # of the cases those two could not settle (adjudicated/ wins over both).
    auto = os.path.join(V, 'auto.json')
    res = {r['id']: r for r in json.load(open(auto, encoding='utf-8'))} if os.path.exists(auto) else load_dir('resolved')
    vpath = os.path.join(V, 'verified_auto.json')
    ver = json.load(open(vpath, encoding='utf-8')) if os.path.exists(vpath) else load_dir('verified')
    adj = load_dir('adjudicated')
    for bid, a in adj.items():
        if a.get('status'):
            res[bid] = {**res.get(bid, {}), **a, 'id': bid}
            ver[bid] = {'verdict': a.get('verdict') or 'corrected', 'evidence_url': a.get('evidence_url'),
                        'note': a.get('note')}
    print('records %d, verdicts %d, adjudicated %d, catalogue %d' % (len(res), len(ver), len(adj), len(valid)))
    stray = sorted(set(res) - valid)
    if stray:
        print('WARN %d resolved ids are not in the catalogue: %s' % (len(stray), ', '.join(stray[:8])))

    recs, stats = {}, collections.Counter()
    for bid in sorted(valid):
        r = res.get(bid)
        if not r:
            stats['no_record'] += 1
            continue
        v = ver.get(bid) or {}
        verdict = v.get('verdict') or ('confirmed' if ASSUME else 'not_reviewed')
        src = r
        if verdict == 'corrected' and isinstance(v.get('corrected'), dict) and v['corrected'].get('status'):
            src = dict(v['corrected'])
        cross = v.get('cross_agree') or []
        status = src.get('status') or 'unclear'
        vid = None
        if status in ('published', 'accepted'):
            hint = (src.get('venue_id_hint') or '').strip()
            vid = hint if any(x['id'] == hint for x in REGISTRY) else \
                canon(src.get('venue_name'), src.get('venue_full'), src.get('venue_kind'),
                      src.get('parent_venue'))
        rec = {
            'status': status,
            'venue': vid,
            'venue_name_raw': clean(src.get('venue_name')),
            'venue_full': clean(src.get('venue_full')),
            'year': clean(str(src.get('venue_year') or '')),
            'kind': clean(src.get('venue_kind')),
            'track': clean(src.get('track')),
            'parent_venue': clean(src.get('parent_venue')),
            'display': clean(src.get('display')),
            'evidence': evidence_bucket(src.get('evidence_url'), src.get('evidence_source')),
            'evidence_raw': clean(src.get('evidence_source')),
            'evidence_url': clean(src.get('evidence_url')),
            'evidence_quote': clean(src.get('evidence_quote')),
            'doi': clean(src.get('doi')),
            'confidence': src.get('confidence') or 'low',
            'verified': verdict,
            'publishable': verdict in ('confirmed', 'corrected'),
            'note': clean(src.get('note')) or clean(v.get('note')),
            'check_url': clean(v.get('evidence_url')),
            'cross_checked': cross or None,
            'check_note': clean(v.get('note')),
        }
        # a venue claim with no evidence link cannot be published as fact
        if rec['status'] in ('published', 'accepted') and not rec['evidence_url'] and not rec['check_url']:
            rec['publishable'] = False
            rec['note'] = ((rec['note'] + ' | ') if rec['note'] else '') + 'no evidence URL - not counted'
        if rec['status'] in ('published', 'accepted') and not rec['display']:
            rec['display'] = ' '.join(x for x in [rec['venue_name_raw'], rec['year']] if x) or None
        recs[bid] = rec
        stats[rec['status']] += 1
        stats['verdict_' + verdict] += 1
        if rec['publishable']:
            stats['publishable'] += 1

    used = {r['venue'] for r in recs.values() if r.get('venue')}
    registry = [v for v in REGISTRY if v['id'] in used]
    payload = {
        'generated': AS_OF, 'as_of': AS_OF,
        'method': ('Resolved from the paper record itself - the arXiv journal-ref and author comment, then the '
                   "venue's own listing (ACL Anthology, ISCA Archive, OpenReview, DBLP, publisher DOI). Every "
                   'verdict was then re-read by a second, independent pass that tried to refute it; only '
                   'confirmed or corrected records are counted.'),
        'venues': sorted(registry, key=lambda v: (v['community'], v['name'].lower())),
        'benchmarks': recs,
    }
    json.dump(payload, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('WROTE %s  benchmarks=%d  venues=%d' % (OUT, len(recs), len(registry)))
    print(json.dumps(dict(stats), indent=1, sort_keys=True))
    un = [v['id'] for v in registry if v.get('unregistered')]
    if un:
        print('UNREGISTERED venue ids (review these): %s' % ', '.join(un))


main()
