#!/usr/bin/env python3
"""Deterministic venue resolution from the harvested primary records.

Priority, strongest first. Each level is a record kept BY THE VENUE ITSELF, so the answer is
quotable rather than asserted:

  1. ACL Anthology entry            -> published   (the ACL family's own archive)
  2. ISCA Archive entry             -> published   (Interspeech / Odyssey / SSW / SLaTE)
  3. Crossref record, non-arXiv DOI -> published   (IEEE, ACM, Springer, MIT Press, AAAI, PMLR)
  4. OpenReview note with a venue and a publication date -> published (ICLR / NeurIPS / ICML / TMLR)
  5. arXiv journal-ref              -> published   (the authors naming the proceedings)
  6. DBLP record, venue != CoRR     -> published
  7. OpenReview note, venue but no publication date -> accepted
  8. arXiv comment claiming acceptance             -> accepted
  9. nothing                                       -> preprint

Writes raw/venue/auto.json plus raw/venue/auto_review.json (the cases a human/agent must settle).
"""
import json, os, re, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(ROOT, 'raw', 'venue')
AS_OF = sys.argv[1] if len(sys.argv) > 1 else None
if not AS_OF:
    sys.exit('usage: resolve_venues.py <as-of YYYY-MM-DD>')


def load(name, default):
    p = os.path.join(V, name)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else default


AX = load('arxiv.json', {})
ANT = load('anthology.json', {})
ISCA = load('isca.json', {})
CR = load('crossref.json', {})
ORV = load('openreview.json', {})
DB = {}
if os.path.isdir(os.path.join(V, 'dblp')):
    for f in os.listdir(os.path.join(V, 'dblp')):
        r = json.load(open(os.path.join(V, 'dblp', f), encoding='utf-8'))
        DB[r['id']] = r.get('hits', [])

# weak matches promoted by adjudicate_weak.py: the candidate record was fetched and found to
# name this very benchmark, so the retitle is established rather than guessed.
PROMOTED = {}
_wa = os.path.join(V, 'weak_accepted.json')
if os.path.exists(_wa):
    for _a in json.load(open(_wa, encoding='utf-8')):
        PROMOTED.setdefault(_a['id'], set()).add((_a['candidate'] or {}).get('url'))


def strong(hits, bid=None):
    """Only exact and fuzzy matches may decide a verdict. 'weak' means the author list matched
    but the title did not - a candidate for review, never an answer, unless adjudication
    confirmed it by finding the benchmark named in the candidate record itself."""
    ok = PROMOTED.get(bid or '', set())
    out = []
    for h in (hits or []):
        m = h.get('_match', 'exact')
        if m in ('exact', 'fuzzy'):
            out.append(h)
        elif m == 'weak' and (h.get('url') in ok or
                              (h.get('doi') and ('https://doi.org/' + h['doi']) in ok)):
            out.append(dict(h, _promoted=True))
    return out


def weak(hits):
    return [h for h in (hits or []) if h.get('_match') == 'weak']


ACC = re.compile(r'\b(accepted|camera[- ]ready|to appear|will appear|published (in|at)|proceedings of)\b', re.I)
SUBM = re.compile(r'\b(submitted to|under review|in submission|under submission)\b', re.I)
TRACK_CLAIM = re.compile(r'\b(LBD|late[- ]breaking(?: demo| results)?|oral|spotlight|poster|'
                         r'demo(?:nstration)?|industry(?: track)?|short paper|main conference|'
                         r'system demonstration)\b', re.I)
TRACK_NAMES = {'lbd': 'Late-Breaking Demo', 'late-breaking': 'Late-Breaking Demo',
               'late breaking': 'Late-Breaking Demo', 'late-breaking demo': 'Late-Breaking Demo',
               'oral': 'Oral', 'spotlight': 'Spotlight', 'poster': 'Poster', 'demo': 'Demo',
               'demonstration': 'Demo', 'industry': 'Industry', 'industry track': 'Industry',
               'short paper': 'Short', 'main conference': 'Main',
               'system demonstration': 'Demo'}
WORKSHOP_RE = re.compile(r'workshop\s*(?:on\s+(?P<topic>[^(,.;]{3,60}))?\s*(?:\((?P<acro>[A-Za-z0-9\-]{2,20})\))?',
                         re.I)

# --- ACL Anthology booktitle -> (venue id, short name, track) -------------------------------
ANT_RULES = [
    (r'^Findings of the Association for Computational Linguistics:?\s*(ACL|EMNLP|NAACL|EACL|IJCNLP|AACL)', 'FINDINGS'),
    (r'Annual Meeting of the Association for Computational Linguistics', ('acl', 'ACL')),
    (r'Conference on Empirical Methods in Natural Language Processing', ('emnlp', 'EMNLP')),
    (r'Conference of the Nations of the Americas Chapter of the Association for Computational Linguistics',
     ('naacl', 'NAACL')),
    (r'North American Chapter of the Association for Computational Linguistics', ('naacl', 'NAACL')),
    (r'Conference of the European Chapter of the Association for Computational Linguistics', ('eacl', 'EACL')),
    (r'Asia-Pacific Chapter of the Association for Computational Linguistics', ('aacl', 'AACL-IJCNLP')),
    (r'International Joint Conference on Natural Language Processing', ('aacl', 'AACL-IJCNLP')),
    (r'International Conference on Computational Linguistics', ('coling', 'COLING')),
    (r'Language Resources and Evaluation Conference', ('lrec', 'LREC')),
    (r'Conference on Computational Natural Language Learning', ('conll', 'CoNLL')),
]
JOURNAL_RULES = [
    (r'Transactions of the Association for Computational Linguistics', ('tacl', 'TACL')),
    (r'^Computational Linguistics$', ('cl', 'Computational Linguistics')),
]
TRACK_RE = re.compile(r'\((Volume \d+: [^)]+|System Demonstrations|Industry Track|Student Research Workshop|'
                      r'Tutorial Abstracts|Demonstrations?)\)', re.I)

# --- Crossref container / event -> venue --------------------------------------------------
CR_RULES = [
    (r'\bICASSP\b|Acoustics,? Speech,? and Signal Processing', ('icassp', 'ICASSP', 'conference')),
    (r'Spoken Language Technology Workshop|\bSLT\b', ('slt', 'SLT', 'conference')),
    (r'Automatic Speech Recognition and Understanding|\bASRU\b', ('asru', 'ASRU', 'conference')),
    (r'Applications of Signal Processing to Audio and Acoustics|WASPAA', ('waspaa', 'WASPAA', 'conference')),
    (r'Multimedia and Expo|\bICME\b', ('icme', 'ICME', 'conference')),
    (r'International Conference on Multimedia\b|Multimedia \(MM|\bACM Multimedia\b',
     ('acmmm', 'ACM MM', 'conference')),
    (r'Computer Vision and Pattern Recognition', ('cvpr', 'CVPR', 'conference')),
    (r'International Conference on Computer Vision', ('iccv', 'ICCV', 'conference')),
    (r'European Conference on Computer Vision', ('eccv', 'ECCV', 'conference')),
    (r'Knowledge Discovery and Data Mining', ('kdd', 'KDD', 'conference')),
    (r'Research and Development in Information Retrieval', ('sigir', 'SIGIR', 'conference')),
    (r'Human Factors in Computing Systems', ('chi', 'CHI', 'conference')),
    (r'AAAI Conference on Artificial Intelligence|Proceedings of the AAAI', ('aaai', 'AAAI', 'conference')),
    (r'International Joint Conference on Artificial Intelligence', ('ijcai', 'IJCAI', 'conference')),
    (r'Transactions of the Association for Computational Linguistics', ('tacl', 'TACL', 'journal')),
    (r'IEEE/ACM Transactions on Audio, Speech,? and Language Processing|'
     r'IEEE Transactions on Audio, Speech,? and Language Processing', ('taslp', 'IEEE/ACM TASLP', 'journal')),
    (r'Computer Speech (and|&amp;|&) Language', ('csl', 'Computer Speech & Language', 'journal')),
    (r'^Speech Communication$', ('speechcom', 'Speech Communication', 'journal')),
    (r'Chinese Spoken Language Processing|ISCSLP', ('iscslp', 'ISCSLP', 'conference')),
    (r'APSIPA', ('apsipa', 'APSIPA ASC', 'conference')),
    (r'Interspeech', ('interspeech', 'Interspeech', 'conference')),
    (r'Music Information Retrieval', ('ismir', 'ISMIR', 'conference')),
    (r'Advances in Neural Information Processing Systems|Neural Information Processing Systems',
     ('neurips', 'NeurIPS', 'conference')),
    (r'International Conference on Learning Representations', ('iclr', 'ICLR', 'conference')),
    (r'International Conference on Machine Learning', ('icml', 'ICML', 'conference')),
    (r'Conference on Language Modeling', ('colm', 'COLM', 'conference')),
    (r'Symposium on Security and Privacy', ('ieee-sp', 'IEEE S&P', 'conference')),
    (r'IEEE Transactions on Artificial Intelligence', ('ieee-tai', 'IEEE TAI', 'journal')),
    (r'COMmunication Systems and NETworks|COMSNETS', ('comsnets', 'COMSNETS', 'conference')),
]
# --- OpenReview venueid -> venue ----------------------------------------------------------
OR_RULES = [
    (r'^ICLR\.cc', ('iclr', 'ICLR')), (r'^NeurIPS\.cc', ('neurips', 'NeurIPS')),
    (r'^ICML\.cc', ('icml', 'ICML')), (r'^TMLR', ('tmlr', 'TMLR')), (r'^colmweb\.org', ('colm', 'COLM')),
    (r'^aclweb\.org', ('acl', 'ACL')), (r'^AAAI\.org', ('aaai', 'AAAI')),
]


def year_of(s):
    s = str(s or '')
    m = re.search(r'\b(19|20)\d{2}\b', s)
    if m:
        return m.group(0)
    m = re.search(r'(?<![0-9])(19|20)\d{2}(?![0-9])', s)   # authors write "ICLR2026"
    return m.group(0) if m else ''


def tidy(name, yr=''):
    """Strip a year glued to, or wrapping, the venue name, so the display string is built once
    from (name, year) instead of repeating the year or dropping it."""
    n = (name or '').strip()
    n = re.sub(r'^\s*(19|20)\d{2}\s+', '', n)                 # "2026 IEEE Symposium on ..."
    n = re.sub(r'\s*(19|20)\d{2}\s*$', '', n)                 # "Interspeech 2026"
    n = re.sub(r'([A-Za-z])(19|20)\d{2}$', r'\1', n)           # "ICLR2026"
    n = re.sub(r'^\s*\d+(st|nd|rd|th)\s+', '', n)
    n = re.sub(r"\s*\([^()]*'?\d{2,4}\)\s*$", '', n)      # "ACM Multimedia 2026 (MM '26)"
    n = re.sub(r'\s*(19|20)\d{2}\s*$', '', n)
    return n.strip(' -:,') or (name or '').strip()


def disp(name, yr='', track=''):
    n = tidy(name, yr)
    out = ('%s %s' % (n, yr)).strip() if yr else n
    return ('%s %s' % (out, track)).strip() if track else out


def rec(status, **kw):
    r = {'status': status, 'venue_name': '', 'venue_full': '', 'venue_year': '', 'venue_kind': '',
         'track': '', 'parent_venue': '', 'display': '', 'evidence_source': '', 'evidence_url': '',
         'evidence_quote': '', 'doi': '', 'confidence': 'high', 'checked': [], 'note': '',
         'venue_id_hint': '', 'needs_review': False}
    r.update(kw)
    return r


def from_anthology(hits):
    e = hits[0]
    book = e.get('booktitle') or ''
    jour = e.get('journal') or ''
    yr = e.get('year') or year_of(book) or year_of(jour)
    track = ''
    vid = name = ''
    kind = 'conference'
    for pat, target in JOURNAL_RULES:
        if re.search(pat, jour or '', re.I):
            vid, name = target
            kind = 'journal'
            break
    if not vid:
        for pat, target in ANT_RULES:
            m = re.search(pat, book, re.I)
            if not m:
                continue
            if target == 'FINDINGS':
                fam = m.group(1).upper()
                vid, name = {'ACL': ('acl', 'ACL'), 'EMNLP': ('emnlp', 'EMNLP'), 'NAACL': ('naacl', 'NAACL'),
                             'EACL': ('eacl', 'EACL'), 'IJCNLP': ('aacl', 'AACL-IJCNLP'),
                             'AACL': ('aacl', 'AACL-IJCNLP')}[fam]
                track = 'Findings'
            else:
                vid, name = target
                tm = TRACK_RE.search(book)
                if tm:
                    track = tm.group(1)
            break
    if not vid:
        kind = 'workshop' if re.search(r'workshop', book, re.I) else 'other'
        name = re.sub(r'^Proceedings of (the )?', '', book).strip()
        # workshops print their own acronym: "... for Music and Audio (NLP4MusA 2026)"
        am = re.search(r'\(([A-Za-z][A-Za-z0-9&+\-]{1,15})(?:\s+(?:19|20)\d{2})?\)', name)
        if am and not am.group(1).islower():
            name = am.group(1)
        return rec('published', venue_name=name[:80], venue_full=book, venue_year=yr, venue_kind=kind,
                   display=(name[:70] + (' ' + yr if yr and yr not in name else '')).strip(),
                   evidence_source='acl_anthology', evidence_url=e.get('url'),
                   evidence_quote=book or jour, doi=e.get('doi') or '',
                   checked=['ACL Anthology %s' % e.get('anthology_id')], needs_review=True,
                   note='Anthology booktitle did not match a known venue pattern - check the short name')
    shown = ('Findings of %s' % disp(name, yr)) if track == 'Findings' else disp(name, yr)
    return rec('published', venue_name=name, venue_full=book or jour, venue_year=yr, venue_kind=kind,
               track='' if track == 'Findings' else track, display=shown,
               evidence_source='acl_anthology', evidence_url=e.get('url'),
               evidence_quote=book or jour, doi=e.get('doi') or '',
               venue_id_hint=vid, checked=['ACL Anthology %s' % e.get('anthology_id')])


def from_isca(hits):
    e = hits[0]
    ev = e['event']
    name, yr = ev.rsplit(' ', 1)
    return rec('published', venue_name=name, venue_full='%s (ISCA Archive)' % ev, venue_year=yr,
               venue_kind='conference', display=disp(name, yr), evidence_source='isca_archive',
               evidence_url=e['url'], evidence_quote=e['title'],
               venue_id_hint={'Interspeech': 'interspeech', 'Odyssey': 'odyssey', 'SSW': 'ssw'}.get(name, ''),
               checked=['ISCA Archive %s' % e['slug']])


def from_crossref(hits):
    e = None
    for h in hits:                       # prefer a proceedings/journal record over anything else
        if h.get('type') in ('proceedings-article', 'journal-article', 'book-chapter'):
            e = h
            break
    e = e or hits[0]
    cont = e.get('container') or e.get('event') or ''
    yr = ''
    for key in ('published_print', 'issued', 'event_start'):
        parts = e.get(key) or []
        if parts and parts[0]:            # Crossref writes [None] for a missing date
            yr = str(parts[0])
            break
    yr = yr or year_of(cont)
    vid = name = ''
    kind = 'journal' if e.get('type') == 'journal-article' else 'conference'
    for pat, (v, n, k) in CR_RULES:
        if re.search(pat, cont, re.I) or re.search(pat, e.get('event') or '', re.I):
            vid, name, kind = v, n, k
            break
    if re.search(r'workshop', cont, re.I) and not vid:
        kind = 'workshop'
    if not name:
        name = tidy(re.sub(r'^Proceedings of (the )?', '', cont).strip()[:80], yr)
    return rec('published', venue_name=name, venue_full=cont, venue_year=yr, venue_kind=kind,
               display=disp(name, yr), evidence_source='publisher',
               evidence_url=e.get('url') or ('https://doi.org/' + (e.get('doi') or '')),
               evidence_quote='%s - %s' % (e.get('title', '')[:70], cont), doi=e.get('doi') or '',
               venue_id_hint=vid, checked=['Crossref %s' % e.get('doi')],
               needs_review=not vid,
               note='' if vid else 'Crossref container did not match a known venue - check the short name')


PREPRINT_VENUE = re.compile(r'^\s*(corr|arxiv)\b', re.I)


def from_openreview(hits):
    subs = [h for h in hits if not h['is_dblp_mirror'] and h.get('venue')
            and not PREPRINT_VENUE.match(h['venue'])]
    if not subs:
        return None
    e = None
    for h in subs:                       # a decided venue string beats "Submitted to ..."
        if not re.match(r'^submitted to', h['venue'] or '', re.I):
            e = h
            break
    if not e:
        return None
    ven = e['venue']
    yr = year_of(ven) or year_of(e.get('venueid'))
    vid = name = ''
    for pat, (v, n) in OR_RULES:
        if re.match(pat, e.get('venueid') or '', re.I):
            vid, name = v, n
            break
    if not name:
        name = re.sub(r'\s*(19|20)\d{2}.*$', '', ven).strip() or ven
    track = re.sub(r'^%s\s*%s\s*' % (re.escape(name), yr), '', ven).strip() if yr else ''
    published = bool(e.get('pdate'))
    return rec('published' if published else 'accepted',
               venue_name=name, venue_full=ven, venue_year=yr, venue_kind='conference',
               track=track, display=disp(name, yr, track),
               evidence_source='openreview', evidence_url=e['url'], evidence_quote=ven,
               venue_id_hint=vid, checked=['OpenReview %s' % e.get('forum')],
               needs_review=not vid)


def from_journal_ref(jr, aid):
    yr = year_of(jr)
    vid = name = ''
    kind = 'conference'
    for pat, (v, n, k) in CR_RULES:
        if re.search(pat, jr, re.I):
            vid, name, kind = v, n, k
            break
    if not name:
        for pat, target in ANT_RULES:
            m = re.search(pat, jr, re.I)
            if m and target != 'FINDINGS':
                vid, name = target
                break
    if not name:
        m = re.match(r'\s*(?:Published as a conference paper at\s+)?([A-Z][A-Za-z&/\- ]{1,40}?)\s*(19|20)\d{2}', jr)
        name = (m.group(1).strip() if m else re.sub(r'^Proceedings of (the )?', '', jr).strip()[:60])
    return rec('published', venue_name=name, venue_full=jr, venue_year=yr, venue_kind=kind,
               display=disp(name, yr), evidence_source='arxiv_journal_ref',
               evidence_url='https://arxiv.org/abs/%s' % aid, evidence_quote=jr,
               venue_id_hint=vid, checked=['arXiv journal-ref'], needs_review=not vid)


def from_dblp(hits, aid):
    # DBLP records carry no author list here, so only an exact title may decide a verdict
    pub = [h for h in hits if (h.get('venue') or '') != 'CoRR' and h.get('title_exact')]
    if not pub:
        return None
    e = pub[0]
    ven, yr = e.get('venue') or '', e.get('year') or ''
    vid = name = ''
    kind = 'journal' if e.get('type') == 'Journal Articles' else 'conference'
    for pat, (v, n, k) in CR_RULES:
        if re.search(pat, ven, re.I):
            vid, name, kind = v, n, k
            break
    if not name:
        for pat, target in ANT_RULES + JOURNAL_RULES:
            if target != 'FINDINGS' and re.search(pat, ven, re.I):
                vid, name = target
                break
    if not name and re.match(r'^(ACL|EMNLP|NAACL|EACL|COLING|LREC|NeurIPS|NIPS|ICLR|ICML|AAAI|IJCAI|INTERSPEECH)',
                             ven, re.I):
        key = ven.split()[0].lower()
        vid = {'interspeech': 'interspeech', 'nips': 'neurips'}.get(key, key)
        name = ven.split()[0]
    if not name:
        name = ven[:60]
    return rec('published', venue_name=name, venue_full=ven, venue_year=str(yr), venue_kind=kind,
               display=disp(name, str(yr)), evidence_source='dblp',
               evidence_url=e.get('ee') or e.get('url') or 'https://dblp.org/search?q=',
               evidence_quote='%s %s (DBLP %s)' % (ven, yr, e.get('key')), doi=e.get('doi') or '',
               venue_id_hint=vid, checked=['DBLP %s' % e.get('key')], needs_review=not vid)


def from_comment(comment, aid):
    m = re.search(r'(?:accepted|to appear)\s*(?:as|at|by|to|in|for)?\s*(?:the\s+)?([^.;]{3,90})', comment, re.I)
    claim = (m.group(1).strip() if m else comment[:90])
    yr = year_of(claim) or year_of(comment)
    vid = name = ''
    for pat, (v, n, k) in CR_RULES:
        if re.search(pat, claim, re.I):
            vid, name = v, n
            break
    if not name:
        m2 = re.search(r'\b(ACL|EMNLP|NAACL|EACL|COLING|LREC|CoNLL|NeurIPS|NIPS|ICLR|ICML|AAAI|IJCAI|COLM|TMLR|'
                       r'Interspeech|ICASSP|ASRU|SLT|Odyssey|WASPAA|ISMIR|CVPR|ICCV|ECCV|ACM MM|ICME|TACL)\b',
                       claim, re.I)
        if m2:
            name = m2.group(1)
            vid = {'nips': 'neurips', 'acm mm': 'acmmm'}.get(name.lower(), name.lower())
    if not name:
        name = claim[:60]
    findings = bool(re.search(r'\bfindings\b', claim, re.I))
    # A workshop co-located with a conference is not that conference. But "accepted at
    # INTERSPEECH 2026 and as non-archival paper at ICML 2026 Workshop ..." names two venues;
    # the workshop wording only applies to THIS venue if it follows it immediately.
    wm = WORKSHOP_RE.search(claim)
    if wm and name:
        m_name = re.search(re.escape(name), claim, re.I)
        gap = wm.start() - (m_name.end() if m_name else 0)
        if not m_name or gap < 0 or gap > 30:
            wm = None
    if wm:
        parent = disp(name, yr)
        acro = wm.group('acro')
        topic = (wm.group('topic') or '').strip(' ,.')
        wname = acro or (topic[:44] if topic else 'Workshop')
        shown = ('%s %s Workshop' % (parent, wname)).strip()
        return rec('accepted', venue_name=wname, venue_full=claim, venue_year=yr,
                   venue_kind='workshop', parent_venue=parent, display=shown,
                   evidence_source='arxiv_comment',
                   evidence_url='https://arxiv.org/abs/%s' % aid, evidence_quote=comment[:200],
                   venue_id_hint='', confidence='medium', checked=['arXiv comment'],
                   needs_review=True,
                   note='a co-located workshop, not the parent conference; the authors state '
                        'acceptance and the workshop has no public record of it yet')
    tm = TRACK_CLAIM.search(claim)
    track = TRACK_NAMES.get(tm.group(1).lower(), tm.group(1)) if tm else ''
    shown = ('Findings of %s' % disp(name, yr)) if findings else disp(name, yr, track)
    return rec('accepted', venue_name=tidy(name, yr), venue_full=claim, venue_year=yr,
               track=track, venue_kind='conference', display=shown, evidence_source='arxiv_comment',
               evidence_url='https://arxiv.org/abs/%s' % aid, evidence_quote=comment[:200],
               venue_id_hint=vid, confidence='medium', checked=['arXiv comment'],
               needs_review=not vid,
               note='the authors state acceptance; the venue has no public record of it yet')


def main():
    bench = json.load(open(os.path.join(ROOT, 'data', 'benchmarks.json'), encoding='utf-8'))['entries']
    out, review, stats, srcs = [], [], collections.Counter(), collections.Counter()
    for b in bench:
        bid = b['id']
        aid = b.get('arxiv_id') or ''
        ax = AX.get(aid, {})
        comment, jref = ax.get('comment') or '', ax.get('journal_ref') or ''
        r = None
        if strong(ANT.get(bid), bid):
            r = from_anthology(strong(ANT[bid], bid))
        elif strong(ISCA.get(bid), bid):
            r = from_isca(strong(ISCA[bid], bid))
        elif strong(CR.get(bid), bid):
            r = from_crossref(strong(CR[bid], bid))
        if r is None and strong(ORV.get(bid), bid):
            r = from_openreview(strong(ORV[bid], bid))
        if r is None and jref:
            r = from_journal_ref(jref, aid)
        if r is None and DB.get(bid):
            r = from_dblp(DB[bid], aid)
        if r is None and comment and ACC.search(comment) and not SUBM.search(comment):
            r = from_comment(comment, aid)
        if r is None:
            checked = ['ACL Anthology', 'ISCA Archive', 'Crossref', 'OpenReview', 'arXiv journal-ref/comment']
            if DB.get(bid) is not None:
                checked.append('DBLP')
            r = rec('preprint', evidence_source='arxiv', evidence_url='https://arxiv.org/abs/%s' % aid,
                    evidence_quote=(comment[:160] if comment else 'no journal reference, no acceptance note'),
                    checked=checked,
                    note='not found in any of the indexed archives' + (' (submission note only)' if SUBM.search(comment) else ''))
        r['id'] = bid
        cands = []
        for src, hits in (('ACL Anthology', ANT.get(bid)), ('ISCA Archive', ISCA.get(bid)),
                          ('Crossref', CR.get(bid)), ('OpenReview', ORV.get(bid))):
            for h in weak(hits):
                if h.get('url') in PROMOTED.get(bid, set()):
                    continue
                cands.append({'source': src, 'title': h.get('title'),
                              'venue': h.get('booktitle') or h.get('journal') or h.get('event')
                                       or h.get('container') or h.get('venue'),
                              'url': h.get('url') or (('https://doi.org/' + h['doi']) if h.get('doi') else None),
                              'score': h.get('_score')})
        if cands:
            # same authors, different title: could be this paper retitled, could be the group's
            # next paper. Never auto-accepted; raised so a reviewer settles it.
            r['weak_candidates'] = cands
            r['needs_review'] = True
            r['note'] = (r['note'] + ' | ' if r['note'] else '') +                 '%d same-author record(s) with a different title found - review whether one is this paper retitled' % len(cands)
        out.append(r)
        stats[r['status']] += 1
        srcs[r['evidence_source']] += 1
        if r.get('needs_review'):
            review.append(r)

    json.dump(out, open(os.path.join(V, 'auto.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(review, open(os.path.join(V, 'auto_review.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('resolved %d entries' % len(out))
    print('  status : %s' % dict(stats))
    print('  source : %s' % dict(srcs))
    print('  %d flagged needs_review -> raw/venue/auto_review.json' % len(review))


main()
