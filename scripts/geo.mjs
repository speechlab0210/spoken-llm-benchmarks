// Geography layer for the Atlas build: validates data/institutions.json + data/affiliations.json
// against the catalogue and derives the per-institution / per-country / per-type statistics the
// site renders. Pure functions, no I/O. Imported by build.mjs.
//
// Counting policy (the same everywhere on the page):
//  * only records marked `publishable` (verified by the independent second read, >= 1 institution) count
//  * "any author": a benchmark counts once per distinct institution on its paper, and once per country
//    those occurrences sit in (the occurrence's own country — a London site of a US company counts for GB)
//  * "lead": exactly one institution per benchmark — the first-listed affiliation of the first author
//  * models: one count per releasing organisation; cascades of third-party parts are never attributed

const EUROPE = new Set(['GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'CH', 'AT', 'SE', 'NO', 'DK', 'FI', 'PL', 'CZ', 'PT', 'IE', 'GR', 'HU', 'RO',
  'LU', 'EE', 'LV', 'LT', 'SI', 'HR', 'RS', 'BG', 'SK', 'IS', 'CY', 'MT', 'UA', 'MD', 'BY', 'AL', 'MK', 'BA', 'ME', 'XK']);
export const REGION_ORDER = ['China', 'United States', 'Europe', 'Taiwan', 'Singapore', 'South Korea', 'Japan', 'Other', 'Unknown'];
export const REGION_DEF = {
  'China': 'CN, HK, MO', 'United States': 'US', 'Europe': [...EUROPE].join(', '), 'Taiwan': 'TW', 'Singapore': 'SG',
  'South Korea': 'KR', 'Japan': 'JP', 'Other': 'every other country (incl. Canada, Australia, India, Israel, Russia, Turkey)', 'Unknown': 'no country on file',
};
const REGION_OF = (cc) => {
  if (!cc) return 'Unknown';
  if (cc === 'CN' || cc === 'HK' || cc === 'MO') return 'China';
  if (cc === 'US') return 'United States';
  if (cc === 'TW') return 'Taiwan';
  if (cc === 'SG') return 'Singapore';
  if (cc === 'KR') return 'South Korea';
  if (cc === 'JP') return 'Japan';
  if (EUROPE.has(cc)) return 'Europe';
  return 'Other';
};

export function validateGeo({ institutions, affiliations, benchmarks, models, fail, warn }) {
  const instIds = new Set();
  for (const i of institutions.entries) {
    for (const k of ['id', 'name', 'type']) if (!i[k]) fail(`institution missing ${k}: ${i.id ?? i.name ?? '?'}`);
    if (instIds.has(i.id)) fail(`duplicate institution id: ${i.id}`);
    instIds.add(i.id);
    if (i.country && !/^[A-Z]{2}$/.test(i.country)) fail(`institution ${i.id}: country must be ISO alpha-2, got "${i.country}"`);
    for (const s of i.sites || []) {
      if (typeof s.lat !== 'number' || typeof s.lon !== 'number') fail(`institution ${i.id}: site without numeric lat/lon`);
      if (s.lat < -90 || s.lat > 90 || s.lon < -180 || s.lon > 180) fail(`institution ${i.id}: site out of range ${s.lat},${s.lon}`);
    }
  }
  const benchIds = new Set(benchmarks.entries.map((b) => b.id));
  const modelIds = new Set(models.entries.map((m) => m.id));
  for (const [bid, rec] of Object.entries(affiliations.benchmarks || {})) {
    if (!benchIds.has(bid)) fail(`affiliations.benchmarks: unknown benchmark "${bid}"`);
    if (typeof rec.publishable !== 'boolean') fail(`affiliations.benchmarks[${bid}]: missing publishable flag`);
    const leads = (rec.institutions || []).filter((a) => a.lead).length;
    if (leads > 1) fail(`affiliations.benchmarks[${bid}]: more than one lead institution`);
    if (typeof rec.countries_complete !== 'boolean') fail(`affiliations.benchmarks[${bid}]: countries_complete must be boolean`);
    if (rec.publishable) {
      if (!(rec.institutions || []).length) fail(`affiliations.benchmarks[${bid}]: publishable without institutions`);
      if (!['confirmed', 'corrected'].includes(rec.verified)) fail(`affiliations.benchmarks[${bid}]: publishable but verified="${rec.verified}"`);
      if (rec.status === 'no_affiliation_text') fail(`affiliations.benchmarks[${bid}]: publishable but status=no_affiliation_text`);
      if (rec.verified === 'corrected' && !rec.verify_note) fail(`affiliations.benchmarks[${bid}]: corrected without the checker's quoted reason`);
    }
    for (const a of rec.institutions || []) {
      if (!instIds.has(a.inst)) fail(`affiliations.benchmarks[${bid}]: unknown institution "${a.inst}"`);
      if (a.country && !/^[A-Z]{2}$/.test(a.country)) fail(`affiliations.benchmarks[${bid}]: bad country "${a.country}"`);
      if ((a.lat == null) !== (a.lon == null)) fail(`affiliations.benchmarks[${bid}]: half a coordinate for ${a.inst}`);
      if (a.lat != null && (a.lat < -90 || a.lat > 90 || a.lon < -180 || a.lon > 180)) fail(`affiliations.benchmarks[${bid}]: coordinate out of range for ${a.inst}`);
    }
  }
  for (const [mid, rec] of Object.entries(affiliations.models || {})) {
    if (!modelIds.has(mid)) fail(`affiliations.models: unknown model "${mid}"`);
    if (typeof rec.publishable !== 'boolean') fail(`affiliations.models[${mid}]: missing publishable flag`);
    if (rec.publishable) {
      if (rec.status !== 'ok') fail(`affiliations.models[${mid}]: publishable but status="${rec.status}"`);
      if (!(rec.builders || []).length) fail(`affiliations.models[${mid}]: publishable without builders`);
      if (!(rec.evidence_url && /^https?:\/\//.test(rec.evidence_url))) fail(`affiliations.models[${mid}]: publishable without evidence_url`);
    }
    for (const a of rec.builders || []) if (!instIds.has(a.inst)) fail(`affiliations.models[${mid}]: unknown institution "${a.inst}"`);
  }
  // new catalogue entries may not have an affiliation record yet — allowed, but never silent
  const missingB = benchmarks.entries.filter((b) => !affiliations.benchmarks[b.id]).map((b) => b.id);
  const missingM = models.entries.filter((m) => !affiliations.models[m.id]).map((m) => m.id);
  if (missingB.length) warn(`${missingB.length} benchmark(s) have no affiliation record yet: ${missingB.slice(0, 8).join(', ')}${missingB.length > 8 ? '…' : ''}`);
  if (missingM.length) warn(`${missingM.length} model(s) have no builder record yet: ${missingM.slice(0, 8).join(', ')}${missingM.length > 8 ? '…' : ''}`);
  return { missingB, missingM };
}

// per-entry state shown on cards and used for coverage denominators
export function benchState(rec) {
  if (!rec) return 'not_attributed';                       // no record yet (new entry)
  if (rec.status === 'no_affiliation_text') return 'no_affiliation';   // the paper prints none
  if (!rec.publishable) return 'pending';                  // extracted but the second read did not confirm (or nothing usable came out)
  return rec.status === 'partial' ? 'partial' : 'attributed';
}

export function computeGeo({ institutions, affiliations, benchmarks, models, world }) {
  const instById = Object.fromEntries(institutions.entries.map((i) => [i.id, i]));
  const worldIds = new Set(((world && world.countries) || []).map((c) => c.id).filter(Boolean));
  const countryName = institutions.country_names || {};
  const acc = {};
  const touch = (id) => (acc[id] = acc[id] || { bench_all: new Set(), bench_lead: new Set(), models_all: new Set(), models_lead: new Set(), sites: {} });
  const occSite = (a, i) => {
    if (a.lat != null && a.lon != null) return { city: a.city || null, lat: a.lat, lon: a.lon, placed: a.placed || 'default' };
    const s = (i.sites && i.sites[0]) || null;
    return s ? { city: s.city || null, lat: s.lat, lon: s.lon, placed: 'default' } : null;
  };
  const bumpSite = (id, a, kind, key) => {
    const s = occSite(a, instById[id]); if (!s) return;
    const k = [s.city || '', s.lat, s.lon].join('|');
    const st = acc[id].sites[k] = acc[id].sites[k] || { city: s.city, lat: s.lat, lon: s.lon, bench_all: new Set(), bench_lead: new Set(), models_all: new Set(), named: 0, defaulted: 0 };
    st[kind].add(key);
    if (kind === 'bench_all' || kind === 'models_all') { if (s.placed === 'named') st.named++; else st.defaulted++; }
  };

  const states = { attributed: 0, partial: 0, pending: 0, no_affiliation: 0, not_attributed: 0 };
  const byYearRegion = {};
  const typeSplit = { univ_only: 0, univ_and_company: 0, company_only: 0, neither: 0 };
  let counted = 0, multiInst = 0, multiCountry = 0, multiCountryDenom = 0, leadKnown = 0, unplaced = 0, undated = 0;
  const cAll = {}, cLead = {}, cInst = {};
  for (const b of benchmarks.entries) {
    const rec = affiliations.benchmarks[b.id];
    const st = benchState(rec); states[st]++;
    if (!rec || !rec.publishable) continue;
    counted++;
    const instSet = new Set(rec.institutions.map((a) => a.inst));
    if (instSet.size > 1) multiInst++;
    const countries = new Set(); let hasU = false, hasC = false;
    for (const a of rec.institutions) {
      const i = instById[a.inst]; if (!i) continue;
      touch(a.inst).bench_all.add(b.id);
      bumpSite(a.inst, a, 'bench_all', b.id);
      const cc = a.country || i.country || null;
      if (cc) { countries.add(cc); (cAll[cc] = cAll[cc] || new Set()).add(b.id); (cInst[cc] = cInst[cc] || new Set()).add(a.inst); }
      if (i.type === 'academia') hasU = true;
      if (i.type === 'industry') hasC = true;
      if (!occSite(a, i)) unplaced++;
    }
    if (rec.countries_complete) { multiCountryDenom++; if (countries.size > 1) multiCountry++; }
    if (hasU && hasC) typeSplit.univ_and_company++; else if (hasU) typeSplit.univ_only++; else if (hasC) typeSplit.company_only++; else typeSplit.neither++;
    const lead = rec.institutions.find((a) => a.lead);
    if (lead && instById[lead.inst]) {
      leadKnown++;
      acc[lead.inst].bench_lead.add(b.id);
      bumpSite(lead.inst, lead, 'bench_lead', b.id);
      const cc = lead.country || instById[lead.inst].country || null;
      if (cc) (cLead[cc] = cLead[cc] || new Set()).add(b.id);
      const yr = b.arxiv_date ? b.arxiv_date.slice(0, 4) : null;
      if (!yr) undated++;
      else { const reg = REGION_OF(cc); (byYearRegion[yr] = byYearRegion[yr] || {})[reg] = (byYearRegion[yr][reg] || 0) + 1; }
    }
  }

  let modelsAttributed = 0, modelsComposite = 0, modelsUnknown = 0, modelsIncomplete = 0, modelsNoRecord = 0;
  const cModels = {};
  for (const m of models.entries) {
    const rec = affiliations.models[m.id];
    if (!rec) { modelsNoRecord++; continue; }
    if (rec.status === 'composite') { modelsComposite++; continue; }
    if (!rec.publishable) { if ((rec.builders || []).length) modelsIncomplete++; else modelsUnknown++; continue; }
    modelsAttributed++;
    for (const a of rec.builders) {
      const i = instById[a.inst]; if (!i) continue;
      touch(a.inst).models_all.add(m.id);
      if (a.lead) acc[a.inst].models_lead.add(m.id);
      bumpSite(a.inst, a, 'models_all', m.id);
      const cc = a.country || i.country || null;
      if (cc) { (cModels[cc] = cModels[cc] || new Set()).add(m.id); (cInst[cc] = cInst[cc] || new Set()).add(a.inst); }
    }
  }

  const instRows = Object.entries(acc).map(([id, c]) => {
    const i = instById[id];
    return {
      id, name: i.name, short: i.short || null, type: i.type, country: i.country || null, parent: i.parent || null, confidence: i.confidence || null,
      bench_all: c.bench_all.size, bench_lead: c.bench_lead.size, models_all: c.models_all.size, models_lead: c.models_lead.size,
      bench_ids: [...c.bench_all], lead_ids: [...c.bench_lead], model_ids: [...c.models_all],
      on_map: Object.keys(c.sites).length > 0,
      sites: Object.values(c.sites).map((s) => ({ city: s.city, lat: s.lat, lon: s.lon, bench_all: s.bench_all.size, bench_lead: s.bench_lead.size, models_all: s.models_all.size, named: s.named, defaulted: s.defaulted })),
    };
  }).sort((a, b) => b.bench_all - a.bench_all || b.bench_lead - a.bench_lead || b.models_all - a.models_all || a.name.localeCompare(b.name));

  const ccs = new Set([...Object.keys(cAll), ...Object.keys(cLead), ...Object.keys(cModels)]);
  const countryRows = [...ccs].map((cc) => ({
    code: cc, name: countryName[cc] || cc, region: REGION_OF(cc), has_polygon: worldIds.has((institutions.iso_numeric || {})[cc]),
    bench_all: (cAll[cc] || new Set()).size, bench_lead: (cLead[cc] || new Set()).size,
    models: (cModels[cc] || new Set()).size, institutions: (cInst[cc] || new Set()).size,
  })).sort((a, b) => b.bench_all - a.bench_all || b.bench_lead - a.bench_lead || a.name.localeCompare(b.name));

  const typeRows = {};
  for (const r of instRows) {
    const t = typeRows[r.type] = typeRows[r.type] || { bench_all: new Set(), bench_lead: new Set(), models: new Set(), institutions: 0 };
    t.institutions++;
    r.bench_ids.forEach((x) => t.bench_all.add(x)); r.lead_ids.forEach((x) => t.bench_lead.add(x)); r.model_ids.forEach((x) => t.models.add(x));
  }
  const types = Object.fromEntries(Object.entries(typeRows).map(([k, t]) => [k, { bench_all: t.bench_all.size, bench_lead: t.bench_lead.size, models: t.models.size, institutions: t.institutions }]));

  const years = Object.keys(byYearRegion).sort();
  const regionTotals = {};
  for (const y of years) for (const [r, n] of Object.entries(byYearRegion[y])) regionTotals[r] = (regionTotals[r] || 0) + n;
  const by_year_region = years.map((y) => ({ year: y, total: Object.values(byYearRegion[y]).reduce((a, b) => a + b, 0), regions: byYearRegion[y] }));
  const both = instRows.filter((r) => r.bench_all > 0 && r.models_all > 0).map((r) => ({ id: r.id, name: r.name, bench_all: r.bench_all, models_all: r.models_all }));

  return {
    total_benchmarks: benchmarks.entries.length, states, counted_benchmarks: counted, lead_known: leadKnown,
    multi_institution_benchmarks: multiInst, multi_country_benchmarks: multiCountry, multi_country_denominator: multiCountryDenom,
    occurrences_unplaced: unplaced, lead_undated: undated,
    total_models: models.entries.length, attributed_models: modelsAttributed, composite_models: modelsComposite, unknown_models: modelsUnknown, incomplete_models: modelsIncomplete, models_no_record: modelsNoRecord,
    institutions: instRows, countries: countryRows, types, type_split: typeSplit,
    by_year_region, region_order: REGION_ORDER, region_def: REGION_DEF, region_totals: regionTotals, builders_and_benchmarkers: both,
  };
}
