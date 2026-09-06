"""Apply reviewed field patches without overwriting a divergent future decision."""
import copy
import json
from pathlib import Path


def apply_corrections(dataset, payload, root):
    path = Path(root) / 'data' / 'metadata-corrections.json'
    if not path.exists():
        return payload
    # Resolve every patch on a copy. A conflict leaves the caller's data untouched.
    result = copy.deepcopy(payload)
    patches = json.loads(path.read_text(encoding='utf-8'))['patches']
    for p in patches:
        if p['dataset'] != dataset:
            continue
        records = result[p['section']]
        is_list = isinstance(records, list)
        current = next((r for r in records if r['id'] == p['id']), None) if is_list else records.get(p['id'])
        before, after = p['before'], p['after']
        matches = lambda expected: (current is None if expected is None else
                                    current is not None and all(current.get(k) == v for k, v in expected.items()))
        if matches(after):
            continue
        if not matches(before):
            raise ValueError(f"Metadata correction conflicts with a new value: {dataset}.{p['section']}.{p['id']}. Reconcile the evidence and correction before rebuilding.")
        if after is None:
            if is_list:
                records.remove(current)
            else:
                del records[p['id']]
        elif current is None:
            if is_list:
                records.append(copy.deepcopy(after))
            else:
                records[p['id']] = copy.deepcopy(after)
        else:
            current.update(copy.deepcopy(after))
    return result
