"""Matching a catalogue paper to a record in someone else's index.

Exact title matching is not enough: papers are routinely RETITLED between the arXiv preprint
and the camera-ready ("The Sonar Moment: Benchmarking Audio-Language Models in Audio
Geo-Localization" became "The Sonar Moment: An Audio Geo-Localization Benchmark for
Audio-Language Models"). Matching on title alone reports such a paper as a preprint, which is
the most damaging error this layer can make.

But loose matching is worse than no matching. A shared author plus vaguely similar wording
matches the group's OTHER papers - SpokenWOZ against "Continuous Speech Tokenizer in Text To
Speech" - and a wrong venue published as fact is not recoverable by a reader. Two rules follow:

  * the titles must be substantially the same content words (after stemming), AND
  * author identity is compared on FULL NAMES, never surnames. Four shared surnames (Li, Wang,
    Zhang, Chen) is the norm in this field and means nothing; four shared full names does not
    happen by accident.

The result says whether the match was exact, fuzzy or weak, so a retitled match can be reviewed
rather than trusted silently.
"""
import re

STOP = set('a an the of on in for to and or with without via using by from at as is are be am '
           'towards toward into over under our new we its their it this that these those can '
           'do does more than not no all any some such very much many we you they he she'.split())


def norm(t):
    t = re.sub(r'[{}\\]', '', t or '')
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', t.lower()).split())


def stem(w):
    for suf in ('ations', 'ation', 'ings', 'ing', 'edly', 'ed', 'es', 's'):
        if len(w) > len(suf) + 3 and w.endswith(suf):
            return w[:-len(suf)]
    return w


def tokens(t):
    return {stem(w) for w in norm(t).split() if len(w) > 2 and w not in STOP}


def containment(a, b):
    """Share of the smaller token set covered by the larger one."""
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def head(t):
    """The part before the first colon - usually the system or benchmark name, which survives
    retitling far more often than the descriptive tail."""
    n = norm((t or '').split(':')[0])
    return n if 0 < len(n) <= 40 else ''


def surname(name):
    n = re.sub(r'[{}\\]', '', name or '').strip()
    if ',' in n:
        n = n.split(',')[0]
        return norm(n).split()[-1] if norm(n) else ''
    parts = norm(n).split()
    return parts[-1] if parts else ''


def surnames(names):
    out = []
    for n in names or []:
        s = surname(n)
        if s and s not in STOP and len(s) > 1:
            out.append(s)
    return out


def fullnames(names):
    """A person as an order-independent set of name tokens: 'Gong, Kaixiong' and 'Kaixiong Gong'
    both become frozenset({'gong', 'kaixiong'}). Single-token names are dropped as unusable.

    Surnames alone are useless for identity in this field - Li, Wang, Zhang and Chen match
    hundreds of unrelated papers - so anything leaning on author identity uses these.
    """
    out = set()
    for n in names or []:
        flat = re.sub(r'[{}\\]', ' ', n or '').replace(',', ' ')
        toks = {t for t in norm(flat).split() if len(t) > 1}
        if len(toks) >= 2:
            out.add(frozenset(toks))
    return out


def split_bib_authors(s):
    return [x.strip() for x in re.split(r'\s+and\s+', s or '') if x.strip()]


def match(cat_title, cat_authors, rec_title, rec_authors):
    """Return ('exact' | 'fuzzy' | 'weak' | None, score).

    'weak' is the awkward real case: the author list is effectively identical but the title was
    rewritten wholesale (AV-Odyssey Bench became "Probing Audio-Visual Reasoning in Multimodal
    Language Models through the Lens of Audio"). That is a candidate, not an answer - callers
    must surface it for review rather than publish it.
    """
    if norm(cat_title) and norm(cat_title) == norm(rec_title):
        return 'exact', 1.0
    ct, rt = tokens(cat_title), tokens(rec_title)
    if len(ct) < 3 or len(rt) < 3:
        return None, 0.0
    cont, jac = containment(ct, rt), jaccard(ct, rt)
    sim = max(cont, jac)

    cs, rs = set(surnames(cat_authors)), set(surnames(rec_authors))
    cf, rf = fullnames(cat_authors), fullnames(rec_authors)
    if not (cs or cf) or not (rs or rf):
        # no author list to lean on: the titles alone must be nearly the same
        return ('fuzzy', sim) if (cont >= 0.9 and jac >= 0.75) else (None, sim)

    fo, ffrac = 0, 0.0
    if cf and rf:
        fo = len(cf & rf)
        ffrac = fo / min(len(cf), len(rf))
        strong_authors = (fo >= 2 and ffrac >= 0.5) or ffrac >= 0.75
    else:
        ov = len(cs & rs)
        frac = ov / min(len(cs), len(rs)) if cs and rs else 0.0
        strong_authors = (ov >= 3 and frac >= 0.5) or frac >= 0.75 or (ov >= 2 and len(cs) <= 3)
    if not strong_authors:
        return None, sim

    same_head = bool(head(cat_title)) and head(cat_title) == head(rec_title)
    if same_head and cont >= 0.5:      # same distinctive name, reworded tail: the classic retitle
        return 'fuzzy', max(sim, 0.8)
    if cont >= 0.75 and jac >= 0.6:
        return 'fuzzy', sim
    if fo >= 4 and ffrac >= 0.9:       # same people, unrecognisable title: candidate only
        return 'weak', sim
    return None, sim
