import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { computeGeo } from './geo.mjs';
import { validateCorrections } from './metadata-corrections.mjs';
const read=n=>JSON.parse(readFileSync(new URL('../data/'+n+'.json',import.meta.url),'utf8'));
const institutions=read('institutions'),affiliations=read('affiliations'),venues=read('venues'),benchmarks=read('benchmarks'),models=read('models');
test('a multi-country team counts once per country without inventing a lead country or headquarters',()=>{
 const b=benchmarks.entries.find(b=>b.id==='mseb');
 const g=computeGeo({institutions,affiliations,benchmarks:{entries:[b]},models:{entries:[]},world:null});
 assert.equal(g.institutions.length,1);assert.equal(g.institutions[0].bench_all,1);assert.equal(g.institutions[0].bench_lead,1);
 assert.deepEqual(g.countries.map(c=>c.code).sort(),['DE','US']);
 assert.ok(g.countries.every(c=>c.bench_all===1&&c.bench_lead===0));
 assert.equal(g.multi_country_benchmarks,1);assert.equal(g.institutions[0].on_map,false);
 assert.equal(g.region_totals.Unknown,1);
});
test('paper identity and workshop distinctions survive the build input',()=>{
 for(const k of ['vox-profile','mseb']){assert.equal(venues.benchmarks[k].status,'preprint');assert.equal(venues.benchmarks[k].venue,null);}
 assert.equal(venues.benchmarks.audiorag.venue,'audio-aaai');
 assert.equal(venues.benchmarks['av-speakerbench'].venue,'cvpr-findings');
 assert.equal(venues.benchmarks['voices-of-civilizations'].venue,'ismir-lbd');
 for(const k of ['audiorag','av-speakerbench','voices-of-civilizations'])assert.equal(venues.benchmarks[k].kind,'workshop');
});
test('TWIST variants credit work-time builders consistently, and MIO keeps all collaborators',()=>{
 const builder=k=>affiliations.models[k].builders.map(x=>[x.inst,x.lead]);
 for(const k of ['twist','twist-1-3b','twist-350m'])assert.deepEqual(builder(k),builder('twist-7b'));
 assert.equal(builder('mio-instruct').length,11);
 assert.ok(!builder('f-actor').some(([id])=>id==='natwest'));
});
test('reviewed corrections are present and a stale writer is rejected',()=>{
 const c=read('metadata-corrections'),ds={institutions,affiliations,venues,models};
 const fail=msg=>{throw new Error(msg)};
 validateCorrections(c,ds,fail);
 const stale=structuredClone(ds);stale.venues.benchmarks['vox-profile'].status='published';
 assert.throws(()=>validateCorrections(c,stale,fail),/vox-profile/);
});
test('audit accounts for every record in its dated scope, including exclusions and uncertainty',()=>{
 const a=read('metadata-audit-2026-09-06');
 assert.equal(a.benchmarks.length,383);assert.equal(a.models.length,230);
 assert.equal(new Set(a.benchmarks.map(x=>x.id)).size,383);assert.equal(new Set(a.models.map(x=>x.id)).size,230);
 assert.equal(a.models.filter(x=>x.outcome==='component_cascade_excluded').length,57);
 for(const b of a.benchmarks){assert.ok(b.affiliation.sources.length);assert.ok(b.publication.sources.length);assert.ok(benchmarks.entries.some(x=>x.id===b.id));}
});
