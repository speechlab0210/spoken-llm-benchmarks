import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { buildMetricTables, cellFingerprint, renderMetricAliasAudit } from './metric-aliases.mjs';

const makeRows = (metric, paper, scores = [12.3, 24.6, 37.8]) => scores.map((value, i) => ({
  benchmark: 'bench', model: `model-${i}`, metric, value,
  source: `Paper ${paper}, Table 1`, source_url: `https://arxiv.org/abs/${paper}`,
}));
const member = rows => ({ metric: rows[0].metric, paper: rows[0].source_url.split('/').pop(),
  source_urls: [rows[0].source_url], cell_ids: rows.map(cellFingerprint),
  evidence_url: rows[0].source_url, locator: 'Table 1',
});
const group = (...sets) => ({ version: 1, groups: [{ id: 'approved', benchmark: 'bench',
  label: 'Accuracy (%)', definition: 'Test accuracy, speech input', members: sets.map(member),
}] });
const fixture = () => {
  const a = makeRows('Acc.', '2501.00001'), b = makeRows('Accuracy', '2501.00002');
  return { a, b, cells: [...a, ...b], registry: group(a, b) };
};

test('approved names share one column and retain every source row without mutation', () => {
  const { cells, registry } = fixture(), original = JSON.stringify(cells);
  const out = buildMetricTables(cells, registry);
  assert.equal(out.summary.metric_options, 1);
  assert.equal(out.summary.mapped_observations, 6);
  assert.deepEqual(out.byBenchmark.bench['alias:approved'].models['model-0'], [0, 3]);
  assert.equal(JSON.stringify(cells), original);
});

test('new rows and other benchmarks do not inherit a mapping from their name or paper', () => {
  const { cells, registry, a } = fixture();
  cells.push({ ...a[0], model: 'new-model' }, { ...a[0], benchmark: 'different-benchmark' });
  const out = buildMetricTables(cells, registry);
  assert.deepEqual(out.byBenchmark.bench['raw:Acc.'].models['new-model'], [6]);
  assert.deepEqual(out.byBenchmark['different-benchmark']['raw:Acc.'].models['model-0'], [7]);
  assert.equal(out.summary.mapped_observations, 6);
});

test('a changed value or note invalidates the reviewed fingerprint', () => {
  for (const patch of [{ value: 99 }, { note: 'different input condition' }]) {
    const { cells, registry } = fixture(); Object.assign(cells[0], patch);
    assert.throws(() => buildMetricTables(cells, registry), /stale reviewed observation/);
  }
});

test('one agreeing model, repeated values, and boundary values cannot establish equivalence', () => {
  for (const scores of [[42], [42, 42, 42], [0, 1, 100]]) {
    const a = makeRows('A', '2501.00001', scores), b = makeRows('B', '2501.00002', scores);
    assert.throws(() => buildMetricTables([...a, ...b], group(a, b)), /insufficient cross-paper/);
  }
});

test('versions of the same paper do not count as different sources', () => {
  const a = makeRows('A', '2501.00001'), b = makeRows('B', '2501.00001');
  b.forEach(c => { c.source_url += 'v2'; });
  const registry = group(a, b); registry.groups[0].members[1].paper = '2501.00001';
  assert.throws(() => buildMetricTables([...a, ...b], registry), /cross-paper evidence required/);
});

test('source URLs and cited paper identities must agree', () => {
  const { cells, registry } = fixture();
  registry.groups[0].members[0].evidence_url = 'https://arxiv.org/abs/2501.99999';
  assert.throws(() => buildMetricTables(cells, registry), /missing source evidence/);
  registry.groups[0].members[0].evidence_url = 'https://arxiv.org/abs/2501.00001';
  registry.groups[0].members[0].source_urls = ['https://example.org/2501.00001'];
  assert.throws(() => buildMetricTables(cells, registry), /paper identity mismatch/);
});

test('one contradictory model blocks otherwise matching aliases', () => {
  const { a, b } = fixture();
  a.push({ ...a[0], model: 'conflict', value: 10 }); b.push({ ...b[0], model: 'conflict', value: 20 });
  assert.throws(() => buildMetricTables([...a, ...b], group(a, b)), /contradictory model values/);
});

test('transitive matching cannot join contradictory endpoints', () => {
  const a = makeRows('A', '2501.00001'), b = makeRows('B', '2501.00002');
  const c = makeRows('C', '2501.00003', [45, 56, 67]);
  c.forEach(r => { r.model += '-second'; });
  b.push(...c.map(r => ({ ...b[0], model: r.model, value: r.value })));
  a.push({ ...a[0], model: 'endpoint', value: 10 });
  c.push({ ...c[0], model: 'endpoint', value: 20 });
  assert.throws(() => buildMetricTables([...a, ...b, ...c], group(a, b, c)), /contradictory model values/);
});

test('a source observation cannot enter two approved groups', () => {
  const { cells, registry } = fixture();
  registry.groups.push({ ...structuredClone(registry.groups[0]), id: 'duplicate', label: 'Other' });
  assert.throws(() => buildMetricTables(cells, registry), /assigned more than once/);
});

test('unreviewed repeated cells retain different values, zero, and text verbatim', () => {
  const cells = makeRows('Raw', '2501.00001', [0, '12.3 ± 0.2', '0.8']);
  cells.push({ ...cells[0], value: 1, source: 'Another experiment' });
  const out = buildMetricTables(cells);
  assert.deepEqual(out.byBenchmark.bench['raw:Raw'].models['model-0'], [0, 3]);
  assert.equal(out.summary.observations, 4);
  assert.equal(cells[0].value, 0);
  assert.equal(cells[1].value, '12.3 ± 0.2');
  assert.notEqual(cellFingerprint(cells[2]), cellFingerprint({ ...cells[2], value: 0.8 }));
});

test('current catalogue retains all observations exactly once and includes source audit links', () => {
  const read = name => JSON.parse(readFileSync(new URL(`../data/${name}.json`, import.meta.url), 'utf8'));
  const cells = read('results').cells, registry = read('metric-aliases');
  const original = JSON.stringify(cells), out = buildMetricTables(cells, registry);
  const indices = Object.values(out.byBenchmark).flatMap(metrics => Object.values(metrics).flatMap(m => Object.values(m.models).flat()));
  assert.equal(indices.length, cells.length);
  assert.equal(new Set(indices).size, cells.length);
  assert.equal(JSON.stringify(cells), original);
  const html = renderMetricAliasAudit(registry, read('metric-alias-review-2026-09-10'), out.summary, read('benchmarks'));
  for (const g of registry.groups) {
    assert.ok(html.includes(`id="${g.id}"`));
    assert.ok(html.includes(g.members[0].evidence_url));
  }
});
