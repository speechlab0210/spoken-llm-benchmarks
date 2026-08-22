#!/usr/bin/env node
// Spoken LLM Benchmark Atlas — site builder.
// data/*.json + site-src/template.html -> site/index.html. Deterministic, no network.
// Refuses to build if the data violates the schema gates below.
// Run: node scripts/build.mjs

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => JSON.parse(readFileSync(join(ROOT, p), 'utf8'));
const readOpt = (p, fallback) => (existsSync(join(ROOT, p)) ? read(p) : fallback);

const taxonomy = read('data/taxonomy.json');
const benchmarks = read('data/benchmarks.json');
const models = read('data/models.json');
const results = read('data/results.json');
const editorial = read('data/editorial.json');
const changelog = readOpt('data/changelog.json', { entries: [] });
const latest = readOpt('data/latest.json', { fetched_at: null, candidates: [] });

const fail = (msg) => { throw new Error(`[build] ${msg}`); };

// ---------- gates ----------
if (!Array.isArray(taxonomy.categories) || !taxonomy.categories.length) fail('taxonomy.categories empty');
const catIds = new Set(taxonomy.categories.map((c) => c.id));
for (const c of taxonomy.categories) {
  for (const k of ['id', 'name', 'blurb', 'group']) if (!c[k]) fail(`category missing ${k}: ${c.id ?? '?'}`);
}

if (!Array.isArray(benchmarks.entries) || !benchmarks.entries.length) fail('benchmarks.entries empty');
const benchIds = new Set();
for (const b of benchmarks.entries) {
  for (const k of ['id', 'name', 'summary', 'categories']) if (!b[k]) fail(`benchmark missing ${k}: ${b.id ?? b.name ?? '?'}`);
  if (benchIds.has(b.id)) fail(`duplicate benchmark id: ${b.id}`);
  benchIds.add(b.id);
  if (!Array.isArray(b.categories) || !b.categories.length) fail(`benchmark ${b.id}: categories must be a non-empty array`);
  for (const c of b.categories) if (!catIds.has(c)) fail(`benchmark ${b.id}: unknown category "${c}"`);
  if (b.arxiv_id && !/^\d{4}\.\d{4,5}$/.test(b.arxiv_id)) fail(`benchmark ${b.id}: malformed arxiv_id "${b.arxiv_id}"`);
  if (b.arxiv_date && !/^\d{4}-\d{2}(-\d{2})?$/.test(b.arxiv_date)) fail(`benchmark ${b.id}: malformed arxiv_date "${b.arxiv_date}"`);
  for (const u of [b.url, b.code, b.data].filter(Boolean)) {
    if (!/^https?:\/\//.test(u)) fail(`benchmark ${b.id}: non-http url ${u}`);
  }
}

if (!Array.isArray(models.entries)) fail('models.entries must be an array');
const modelIds = new Set();
for (const m of models.entries) {
  for (const k of ['id', 'name']) if (!m[k]) fail(`model missing ${k}: ${m.id ?? m.name ?? '?'}`);
  if (modelIds.has(m.id)) fail(`duplicate model id: ${m.id}`);
  modelIds.add(m.id);
}

// Every result cell must name a benchmark, a model, a metric, and a source we can click.
if (!Array.isArray(results.cells)) fail('results.cells must be an array');
const badCells = [];
for (const r of results.cells) {
  if (!benchIds.has(r.benchmark)) { badCells.push(`unknown benchmark "${r.benchmark}"`); continue; }
  if (!modelIds.has(r.model)) { badCells.push(`unknown model "${r.model}"`); continue; }
  if (r.value === undefined || r.value === null || r.value === '') { badCells.push(`${r.benchmark}/${r.model}: empty value`); continue; }
  if (!r.metric) { badCells.push(`${r.benchmark}/${r.model}: missing metric`); continue; }
  if (!r.source) { badCells.push(`${r.benchmark}/${r.model}: missing source — every number must be traceable`); }
}
if (badCells.length) fail(`results.json has ${badCells.length} bad cells:\n  ` + badCells.slice(0, 25).join('\n  '));

if (!editorial.contact_email) fail('editorial.contact_email missing');

// ---------- derived ----------
const byCat = Object.fromEntries(taxonomy.categories.map((c) => [c.id, 0]));
for (const b of benchmarks.entries) for (const c of b.categories) byCat[c] += 1;

const dated = benchmarks.entries.filter((b) => b.arxiv_date);
const since2025 = dated.filter((b) => b.arxiv_date >= '2025-01').length;

const stats = {
  benchmarks: benchmarks.entries.length,
  since_2025: since2025,
  pre_2025: dated.filter((b) => b.arxiv_date < '2025-01').length,
  undated: benchmarks.entries.length - dated.length,
  models: models.entries.length,
  result_cells: results.cells.length,
  categories: taxonomy.categories.length,
  by_category: byCat,
};

const data = {
  built_at: new Date().toISOString(),
  stats,
  taxonomy,
  benchmarks,
  models,
  results,
  editorial,
  changelog,
  latest,
};

const template = readFileSync(join(ROOT, 'site-src', 'template.html'), 'utf8');
if (!template.includes('__ATLAS_DATA__')) fail('template.html missing __ATLAS_DATA__ placeholder');
// </ escaped so embedded JSON can never close the script tag
const payload = JSON.stringify(data).replace(/</g, '\\u003c');
const html = template.replace('"__ATLAS_DATA__"', payload);

mkdirSync(join(ROOT, 'site'), { recursive: true });
writeFileSync(join(ROOT, 'site', 'index.html'), html);
console.log(
  `[atlas] built site/index.html: ${stats.benchmarks} benchmarks ` +
  `(${stats.since_2025} since 2025), ${stats.models} models, ${stats.result_cells} result cells, ` +
  `${(html.length / 1024).toFixed(0)} KB`,
);
