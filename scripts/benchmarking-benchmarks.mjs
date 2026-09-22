import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const escape = x => String(x).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const bi = pair => `<span data-lang="en">${escape(pair[0])}</span><span data-lang="zh">${escape(pair[1])}</span>`;
export function buildBenchmarkingBenchmarks(root) {
  const data = JSON.parse(readFileSync(join(root,'data/benchmarking-benchmarks.json'),'utf8'));
  const notes = JSON.parse(readFileSync(join(root,'data/benchmarking-benchmarks-notes.json'),'utf8')).notes;
  const ids = new Set();
  for (const p of data.papers) {
    if (ids.has(p.id)) throw Error(`Duplicate literature identity: ${p.id}`);
    if (!/^https:\/\/(arxiv\.org|aclanthology\.org|www\.isca-archive\.org)\//.test(p.url)) throw Error(`Non-primary URL: ${p.id}`);
    if (!p.title || !/^\d{4}(-\d{2})?$/.test(p.date)) throw Error(`Missing literature metadata: ${p.id}`);
    if (data.exclusions.some(e=>e.id===p.id)) throw Error(`Excluded paper included: ${p.id}`);
    ids.add(p.id);
  }
  if (new Set(notes.map(n=>n.id)).size!==notes.length) throw Error('Duplicate reading notes');
  for (const n of notes) {
    if (!ids.has(n.id)) throw Error(`Reading note without source: ${n.id}`);
    for (const key of ['target','finding','boundary']) if (!Array.isArray(n[key]) || n[key].length!==2 || n[key].some(s=>!s)) throw Error(`Incomplete translation: ${n.id}/${key}`);
  }
  const cards = notes.map((n,i) => {
    const p=data.papers.find(p=>p.id===n.id);
    return `<article class="paper" data-id="${escape(p.id)}" data-topic="${escape(n.topic)}" id="paper-${escape(p.id)}">
    <div class="paper-top"><span class="paper-no">${String(i+1).padStart(2,'0')}</span><span>${escape(p.date)} · ${escape(p.source)}</span></div>
    <h3><a href="${escape(p.url)}" target="_blank" rel="noopener noreferrer">${escape(n.name)} <span aria-hidden="true">↗</span></a></h3>
    <p class="target">${bi(n.target)}</p><p>${bi(n.finding)}</p>
    <div class="boundary"><strong>${bi(['Read with this boundary','解讀界線'])}</strong><p>${bi(n.boundary)}</p></div>
    <details><summary>${bi(['Full title & source','完整篇名與來源'])}</summary><p>${escape(p.title)}</p><a href="${escape(p.url)}" target="_blank" rel="noopener noreferrer">${escape(p.id)} ↗</a></details></article>`;
  }).join('\n');
  const rows=data.papers.map(p=>`<tr data-id="${escape(p.id)}"><td class="date">${escape(p.date)}</td><td><a href="${escape(p.url)}" target="_blank" rel="noopener noreferrer">${escape(p.title)} <span aria-hidden="true">↗</span></a><div class="ref-meta">${escape(p.source)} · ${escape(p.id)}</div></td><td>${notes.some(n=>n.id===p.id)?bi(['Reading note','有導讀']):bi(['Metadata match','書目核對'])}</td></tr>`).join('\n');
  let template=readFileSync(join(root,'site-src/benchmarking-benchmarks.html'),'utf8');
  const values={__PAPER_COUNT__:String(data.papers.length),__NOTE_COUNT__:String(notes.length),__READING_CARDS__:cards,__REFERENCE_ROWS__:rows,__LITERATURE_DATA__:JSON.stringify({papers:data.papers,notes}).replace(/</g,'\\u003c')};
  for(const [key,value] of Object.entries(values)) {
    if(!template.includes(key)) throw Error(`Missing template marker: ${key}`);
    template=template.replaceAll(key,()=>value);
  }
  for (const dir of [root,join(root,'site')]) {
    writeFileSync(join(dir,'benchmarking-benchmarks.html'),template);
    writeFileSync(join(dir,'benchmarking-benchmarks-catalogue.json'),JSON.stringify(data,null,2)+'\n');
  }
  console.log(`[meta-evaluation] ${data.papers.length} references, ${notes.length} reading notes; excluded ${data.exclusions.length} withdrawn paper`);
}
