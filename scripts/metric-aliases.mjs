import { createHash } from 'node:crypto';

export function cellFingerprint(c) {
  const value = [typeof c.value, String(c.value)];
  const fields = [c.benchmark, c.model, c.metric, value, c.source, c.source_url ?? null, c.note ?? null];
  return createHash('sha256').update(JSON.stringify(fields)).digest('hex');
}

const paperId = url => /^https:\/\/arxiv\.org\/(?:html|abs|pdf)\/(\d{4}\.\d{4,5})(?:v\d+)?(?:\.pdf)?(?:[#?].*)?$/.exec(url)?.[1];

// Every approved mapping pins an original observation, not an unrestricted name.
// A newly imported result therefore needs review before joining an alias group.
export function buildMetricTables(cells, registry = { version: 1, groups: [] }) {
  const fail = msg => { throw new Error(`[metric aliases] ${msg}`); };
  if (registry.version !== 1 || !Array.isArray(registry.groups)) fail('unsupported registry');
  const sourceById = new Map();
  cells.forEach((c, i) => {
    const id = cellFingerprint(c);
    if (!sourceById.has(id)) sourceById.set(id, []);
    sourceById.get(id).push(i);
  });
  const assignment = new Map(), ids = new Set(), publicGroups = [];
  let mapped = 0;
  for (const g of registry.groups) {
    if (!g.id || ids.has(g.id)) fail(`duplicate/missing group id: ${g.id}`);
    ids.add(g.id);
    if (!g.benchmark || !g.label || !g.definition || !Array.isArray(g.members) || g.members.length < 2) fail(`incomplete group ${g.id}`);
    const modelValues = new Map(), aliases = [], papers = new Set(), memberValues = [];
    for (const member of g.members) {
      if (!member.metric || !member.paper || !member.locator || paperId(member.evidence_url) !== member.paper) fail(`missing source evidence in ${g.id}`);
      if (!Array.isArray(member.source_urls) || !member.source_urls.length || member.source_urls.some(url => paperId(url) !== member.paper)) fail(`paper identity mismatch in ${g.id}`);
      if (!Array.isArray(member.cell_ids) || !member.cell_ids.length) fail(`empty member in ${g.id}`);
      const values = new Map();
      memberValues.push(values);
      papers.add(member.paper);
      aliases.push({ metric: member.metric, paper: member.paper, evidence_url: member.evidence_url, locator: member.locator });
      for (const id of member.cell_ids) {
        if (!sourceById.has(id)) fail(`stale reviewed observation in ${g.id}: ${id}`);
        if (assignment.has(id)) fail(`observation assigned more than once: ${id}`);
        for (const index of sourceById.get(id)) {
          const c = cells[index];
          if (c.benchmark !== g.benchmark || c.metric !== member.metric || !member.source_urls.includes(c.source_url)) fail(`source scope mismatch in ${g.id}`);
          const value = JSON.stringify([typeof c.value, c.value]);
          if (modelValues.has(c.model) && modelValues.get(c.model) !== value) fail(`contradictory model values in ${g.id}/${c.model}`);
          modelValues.set(c.model, value);
          values.set(c.model, c.value);
          mapped++;
        }
        assignment.set(id, g.id);
      }
    }
    if (papers.size < 2) fail(`cross-paper evidence required in ${g.id}`);
    // Every member must be connected by reviewed, cross-paper evidence. Three
    // agreeing values do not override a conflicting value elsewhere in a group.
    const connected = new Set([0]);
    let grew = true;
    while (grew) {
      grew = false;
      for (const a of connected) for (let b = 0; b < g.members.length; b++) {
        if (connected.has(b) || g.members[a].paper === g.members[b].paper || g.members[a].metric === g.members[b].metric) continue;
        const matches = [...memberValues[a]].filter(([model, value]) => typeof value === 'number' && Number.isFinite(value) && memberValues[b].get(model) === value);
        const distinct = new Set(matches.map(([, value]) => value).filter(value => ![0, 1, 100].includes(value)));
        if (matches.length >= 3 && distinct.size >= 3) { connected.add(b); grew = true; }
      }
    }
    if (connected.size !== g.members.length) fail(`insufficient cross-paper matching evidence in ${g.id}`);
    publicGroups.push({ id: g.id, benchmark: g.benchmark, label: g.label, definition: g.definition, aliases, source_count: papers.size });
  }
  const groupsById = new Map(publicGroups.map(g => [g.id, g]));
  const byBenchmark = {}, rawNames = {}, byBenchmarkStats = {};
  cells.forEach((c, i) => {
    rawNames[c.benchmark] ??= new Set(); rawNames[c.benchmark].add(c.metric);
    const groupId = assignment.get(cellFingerprint(c));
    const key = groupId ? `alias:${groupId}` : `raw:${c.metric}`;
    const metrics = byBenchmark[c.benchmark] ??= {};
    const entry = metrics[key] ??= { label: groupId ? groupsById.get(groupId).label : c.metric, group_id: groupId ?? null, models: {} };
    (entry.models[c.model] ??= []).push(i);
  });
  let before = 0, after = 0, multiSourceCells = 0;
  for (const [bid, metrics] of Object.entries(byBenchmark)) {
    const labels = new Map();
    for (const [key, entry] of Object.entries(metrics)) {
      if (labels.has(entry.label)) {
        // Unreviewed observations with the same text are not silently absorbed.
        const other = metrics[labels.get(entry.label)];
        if (!entry.group_id) entry.label += ' · other sources';
        else if (!other.group_id) other.label += ' · other sources';
        else fail(`ambiguous reviewed label on ${bid}: ${entry.label}`);
      }
      labels.set(entry.label, key);
      multiSourceCells += Object.values(entry.models).filter(indices => indices.length > 1).length;
    }
    byBenchmarkStats[bid] = { before: rawNames[bid].size, after: Object.keys(metrics).length };
    before += rawNames[bid].size; after += Object.keys(metrics).length;
  }
  return { byBenchmark, groups: publicGroups, summary: {
    groups: publicGroups.length, benchmarks: new Set(publicGroups.map(g => g.benchmark)).size,
    mapped_observations: mapped, observations: cells.length, raw_metric_options: before,
    metric_options: after, multi_source_cells: multiSourceCells, by_benchmark: byBenchmarkStats,
  } };
}

const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]));
export function renderMetricAliasAudit(registry, ledger, tableSummary, benchmarks) {
  const names = new Map(benchmarks.entries.map(b => [b.id, b.name]));
  const s = ledger.summary;
  const rows = registry.groups.map(g => `<details id="${esc(g.id)}"><summary><b>${esc(names.get(g.benchmark) || g.benchmark)}</b> — ${esc(g.label)} <small>${g.members.length} source-scoped names · ${g.observation_count} observations</small></summary><p>${esc(g.definition)}. Only the reviewed source observations below join this group.</p><ul>${g.members.map(m => `<li><a href="${esc(m.evidence_url)}" target="_blank" rel="noopener">${esc(m.paper)}</a>: <strong>${esc(m.metric)}</strong> <span>— ${esc(m.locator)}</span></li>`).join('')}</ul></details>`).join('');
  const held = ledger.pairs.filter(p => p.status !== 'approved' && p.matched_models >= 3 && !p.conflicting_models);
  return `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Reviewed metric aliases — Spoken LLM Benchmark Atlas</title><style>body{font:16px/1.65 system-ui,sans-serif;max-width:1050px;margin:40px auto;padding:0 20px;color:#25352f;background:#faf9f4}a{color:#11674f}h1{line-height:1.2}small{display:block;color:#66756d;font-weight:400}details{border:1px solid #d8ded7;border-radius:8px;padding:14px 18px;margin:12px 0;background:white}summary{cursor:pointer;overflow-wrap:anywhere}li{margin:10px 0;overflow-wrap:anywhere}.stats{font-size:1.2em;padding:18px;background:#e9f0e7;border-radius:8px}table{width:100%;border-collapse:collapse;font-size:14px}td,th{text-align:left;border-bottom:1px solid #d8ded7;padding:10px;vertical-align:top;overflow-wrap:anywhere}@media(max-width:650px){body{padding:0 12px}td,th{padding:7px;font-size:12px}}</style><a href="./#tables">← Back to comparison tables</a><h1>Reviewed metric aliases</h1><p>Reviewed ${esc(registry.reviewed_on)}. This audit was performed by an AI agent using the cited source tables. It groups aliases in published results; it is not a new evaluation of the models or a claim that separate papers performed independent replications.</p><p class="stats"><strong>${s.groups}</strong> groups across <strong>${s.benchmarks}</strong> benchmarks · <strong>${s.source_scoped_names}</strong> source-scoped names · <strong>${s.mapped_observations}</strong> original observations preserved</p><p>Matching scores on at least three common models, with at least three distinct non-boundary values, identify candidates. Source-table review checks the measured quantity, subset and input condition. Full-group value conflicts block transitive merges. One coincident score, a correlation, or a similar name is insufficient. Distinct sources can quote the same earlier result.</p><p>Unresolved sources and conditions remain separate. Multiple evidence groups for the same apparent quantity carry a source-paper suffix when joining them would introduce conflicts. Original metric names, values, source links and notes remain available in each table cell.</p><p>Of ${s.strong_pairs_reviewed} stronger candidate pairs reviewed, ${s.strong_decisions.approved || 0} support approved groups and ${(s.strong_decisions.held || 0)+(s.strong_decisions.rejected || 0)} remain separate. These are pair decisions, not the number of metrics removed. Table options across all benchmarks: ${tableSummary.raw_metric_options} before → ${tableSummary.metric_options} after.</p><p><a href="data/metric-aliases.json">Pinned alias definitions (JSON)</a> · <a href="data/metric-alias-review-2026-09-10.json">All ${s.candidate_pairs} candidate-pair decisions (JSON)</a></p><h2>Approved groups</h2>${rows}<h2>Examples retained separately</h2><p>The full ledger also retains pairs with too little overlap or contradictory values.</p><table><thead><tr><th>Benchmark</th><th>Source metric names</th><th>Reason</th></tr></thead><tbody>${held.map(p=>`<tr><td>${esc(names.get(p.benchmark)||p.benchmark)}</td><td>${esc(p.a.metric)} (${esc(p.a.paper)})<br>${esc(p.b.metric)} (${esc(p.b.paper)})</td><td>${esc(p.reason)}</td></tr>`).join('')}</tbody></table></html>`;
}
