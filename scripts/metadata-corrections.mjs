import { isDeepStrictEqual } from 'node:util';

// Builders apply the reviewed corrections. This gate catches any other writer
// reintroducing the old values, and asks for reconciliation of future changes.
export function validateCorrections(corrections, datasets, fail) {
  for (const p of corrections?.patches || []) {
    const records = datasets[p.dataset]?.[p.section];
    const current = Array.isArray(records) ? records.find(r => r.id === p.id) : records?.[p.id];
    const matches = p.after === null ? !current : current &&
      Object.entries(p.after).every(([k, v]) => isDeepStrictEqual(current[k] ?? null, v));
    if (!matches) fail(`reviewed metadata correction missing or changed: ${p.dataset}.${p.section}.${p.id}; reconcile data/metadata-corrections.json with the new evidence`);
  }
}
