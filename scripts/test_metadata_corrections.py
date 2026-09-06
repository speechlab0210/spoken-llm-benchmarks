import copy
import json
import tempfile
import unittest
from pathlib import Path
from metadata_corrections import apply_corrections


class CorrectionTests(unittest.TestCase):
    def test_rebuild_keeps_new_unrelated_fields_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/'data';p.mkdir()
            patch={'dataset':'venues','section':'benchmarks','id':'same-team-other-paper',
                   'before':{'status':'published'},'after':{'status':'preprint'}}
            (p/'metadata-corrections.json').write_text(json.dumps({'patches':[patch]}))
            source={'benchmarks':{'same-team-other-paper':{'status':'published','new_field':'retain'}}}
            fixed=apply_corrections('venues',source,root)
            self.assertEqual(fixed['benchmarks']['same-team-other-paper'],{'status':'preprint','new_field':'retain'})
            self.assertEqual(apply_corrections('venues',fixed,root),fixed)
            self.assertEqual(source['benchmarks']['same-team-other-paper']['status'],'published')

    def test_future_conflict_leaves_all_input_untouched(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/'data';p.mkdir()
            patches=[{'dataset':'venues','section':'benchmarks','id':key,
                      'before':{'status':'published'},'after':{'status':'preprint'}} for key in ['first','later']]
            (p/'metadata-corrections.json').write_text(json.dumps({'patches':patches}))
            source={'benchmarks':{'first':{'status':'published'},'later':{'status':'accepted'}}};original=copy.deepcopy(source)
            with self.assertRaisesRegex(ValueError,'later'):apply_corrections('venues',source,root)
            self.assertEqual(source,original)

    def test_canonical_registry_addition_and_removal(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/'data';p.mkdir()
            old={'id':'campus','name':'Campus'};new={'id':'institute','name':'Institute'}
            patches=[{'dataset':'institutions','section':'entries','id':'campus','before':old,'after':None},
                     {'dataset':'institutions','section':'entries','id':'institute','before':None,'after':new}]
            (p/'metadata-corrections.json').write_text(json.dumps({'patches':patches}))
            fixed=apply_corrections('institutions',{'entries':[old]},root)
            self.assertEqual(fixed,{'entries':[new]})
            self.assertEqual(apply_corrections('institutions',fixed,root),fixed)
