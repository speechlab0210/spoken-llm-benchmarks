// Venue layer: validation gates + derived statistics for the "Where they were published" section.
// Mirrors geo.mjs — build.mjs owns the file reads, this owns the rules.

const STATUSES = new Set(['published', 'accepted', 'preprint', 'unclear']);
const VERDICTS = new Set(['confirmed', 'corrected', 'cannot_verify', 'not_reviewed']);

export function validateVenues({ venues, benchmarks, fail, warn }) {
  if (!venues || !venues.benchmarks) return;
  const benchIds = new Set(benchmarks.entries.map((b) => b.id));
  const venueIds = new Set((venues.venues || []).map((v) => v.id));

  for (const v of venues.venues || []) {
    for (const k of ['id', 'name', 'kind', 'community']) {
      if (!v[k]) fail(`venue registry entry missing ${k}: ${v.id ?? '?'}`);
    }
  }

  for (const [id, r] of Object.entries(venues.benchmarks)) {
    if (!benchIds.has(id)) fail(`venues.json: record for unknown benchmark "${id}"`);
    if (!STATUSES.has(r.status)) fail(`venues.json ${id}: unknown status "${r.status}"`);
    if (r.verified && !VERDICTS.has(r.verified)) fail(`venues.json ${id}: unknown verdict "${r.verified}"`);
    const claimed = r.status === 'published' || r.status === 'accepted';
    if (claimed) {
      if (!r.venue) fail(`venues.json ${id}: status "${r.status}" with no venue id`);
      if (!venueIds.has(r.venue)) fail(`venues.json ${id}: unknown venue "${r.venue}"`);
      if (!r.display) fail(`venues.json ${id}: status "${r.status}" with no display string`);
      // the rule that makes this layer worth anything: a venue claim shown as fact must be traceable
      const url = r.evidence_url || r.check_url;
      if (r.publishable && !/^https?:\/\//.test(url || '')) {
        fail(`venues.json ${id}: counted as ${r.status} at ${r.display} with no evidence URL — every venue claim must be traceable`);
      }
    } else if (r.venue) {
      fail(`venues.json ${id}: status "${r.status}" must not carry a venue id`);
    }
    if (r.year && !/^\d{4}$/.test(String(r.year))) fail(`venues.json ${id}: malformed year "${r.year}"`);
  }

  const missing = benchmarks.entries.filter((b) => !venues.benchmarks[b.id]);
  if (missing.length) {
    warn(`${missing.length} benchmark(s) have no venue record yet — shown as "not yet checked": ` +
      missing.slice(0, 12).map((b) => b.id).join(', ') + (missing.length > 12 ? ' …' : ''));
  }
}

const COMMUNITY_NAMES = {
  speech: 'Speech (ISCA / IEEE SPS)',
  nlp: 'NLP (ACL family)',
  ml: 'Machine learning & AI',
  'vision-mm': 'Vision & multimedia',
  'audio-music': 'Audio & music IR',
  other: 'Other',
};

export function computeVenues({ venues, benchmarks }) {
  if (!venues || !venues.benchmarks || !Object.keys(venues.benchmarks).length) return null;

  const reg = new Map((venues.venues || []).map((v) => [v.id, v]));
  const entries = benchmarks.entries;
  const rec = (id) => venues.benchmarks[id] || null;

  // ---- headline states. "counted" = second read confirmed or corrected it (same rule as the
  // institution layer). Everything else is shown on its record but never enters a number.
  const states = { confirmed: 0, corrected: 0, cannot_verify: 0, not_reviewed: 0, no_record: 0 };
  const status = { published: 0, accepted: 0, preprint: 0, unclear: 0, unchecked: 0 };
  for (const b of entries) {
    const r = rec(b.id);
    if (!r) { states.no_record += 1; status.unchecked += 1; continue; }
    states[r.verified || 'not_reviewed'] = (states[r.verified || 'not_reviewed'] || 0) + 1;
    if (r.publishable) status[r.status] += 1;
    else status.unchecked += 1;
  }
  const counted = status.published + status.accepted + status.preprint + status.unclear;

  // ---- per venue
  const vmap = new Map();
  for (const b of entries) {
    const r = rec(b.id);
    if (!r || !r.publishable || !r.venue) continue;
    if (!vmap.has(r.venue)) {
      const v = reg.get(r.venue) || { id: r.venue, name: r.venue, kind: 'other', community: 'other' };
      vmap.set(r.venue, { ...v, published: 0, accepted: 0, total: 0, benchmarks: [], years: {} });
    }
    const v = vmap.get(r.venue);
    v[r.status] += 1;
    v.total += 1;
    v.benchmarks.push(b.id);
    if (r.year) v.years[r.year] = (v.years[r.year] || 0) + 1;
  }
  const venueRank = [...vmap.values()].sort((a, b) => b.total - a.total || a.name.localeCompare(b.name));

  // ---- community split (a benchmark lands in exactly one, via its venue)
  const communities = {};
  for (const v of venueRank) {
    const c = v.community || 'other';
    communities[c] = (communities[c] || 0) + v.total;
  }
  const communityRows = Object.entries(communities)
    .map(([id, n]) => ({ id, name: COMMUNITY_NAMES[id] || id, n }))
    .sort((a, b) => b.n - a.n);

  // ---- kinds
  const kinds = { conference: 0, workshop: 0, journal: 0, other: 0 };
  for (const v of venueRank) kinds[v.kind in kinds ? v.kind : 'other'] += v.total;

  // ---- by year of first arXiv posting. Recent years are censored, not unpublishable —
  // the site says so rather than letting the reader read a trend into it.
  const years = {};
  for (const b of entries) {
    if (!b.arxiv_date) continue;
    const y = b.arxiv_date.slice(0, 4);
    const r = rec(b.id);
    const row = years[y] || (years[y] = { year: y, published: 0, accepted: 0, preprint: 0, unclear: 0, unchecked: 0, total: 0 });
    row.total += 1;
    if (!r || !r.publishable) row.unchecked += 1;
    else row[r.status] += 1;
  }
  const byYear = Object.values(years).sort((a, b) => a.year.localeCompare(b.year));

  // ---- lag, in whole years only: the venue record gives an edition year, not a date, so
  // anything finer would be invented precision.
  const lags = [];
  for (const b of entries) {
    const r = rec(b.id);
    if (!r || !r.publishable || r.status !== 'published' || !r.year || !b.arxiv_date) continue;
    lags.push(Number(r.year) - Number(b.arxiv_date.slice(0, 4)));
  }
  lags.sort((a, b) => a - b);
  const lagHist = {};
  for (const l of lags) lagHist[l] = (lagHist[l] || 0) + 1;

  // ---- evidence provenance, so a reader can see what the claims rest on
  const evidence = {};
  for (const b of entries) {
    const r = rec(b.id);
    if (!r || !r.publishable || (r.status !== 'published' && r.status !== 'accepted')) continue;
    const e = r.evidence || 'other';
    evidence[e] = (evidence[e] || 0) + 1;
  }

  return {
    as_of: venues.as_of || venues.generated || null,
    method: venues.method || null,
    states,
    status,
    counted,
    total: entries.length,
    venues: venueRank,
    communities: communityRows,
    community_names: COMMUNITY_NAMES,
    kinds,
    by_year: byYear,
    lag: { n: lags.length, median: lags.length ? lags[Math.floor(lags.length / 2)] : null, hist: lagHist },
    evidence,
  };
}
