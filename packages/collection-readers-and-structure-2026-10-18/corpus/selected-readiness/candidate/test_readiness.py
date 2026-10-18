"""Fail-closed selected-publication dimension; no new collection/legal review."""
import copy,json,tempfile,unittest
from pathlib import Path
from common import *
from readiness import *
import package
from test_package import fixture

class SelectedReadiness(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name);self.root,self.proof,self.family=fixture(self.base)
    def tearDown(self):self.temp.cleanup()
    def qualify(self):
        cov=load(self.root/'coverage.json')
        cov.update(publication_bodies_acquired_and_owned=True,legal_structure_qualified=True,source_consistency_complete=True,publication_accepted=True,complete=True,errors=[])
        (self.root/'coverage.json').write_bytes(encoded(cov))
        f=load(self.family)
        for k,v in cov.items():f[k]=copy.deepcopy(v)
        f['formats']['html']['summary']['source_checkpoint_sha256']=file_hash(self.root/'source/checkpoint.json')
        (self.family).write_bytes(encoded(f))
        p=load(self.proof);p.update(status='verified_publication',verification_exit=0,family_verifier_passed=True,acceptance={'coverage_sha256':file_hash(self.root/'coverage.json'),'publication_text_complete':True,'required_nonimage_documents_complete':True,'legal_structure_qualified':True,'publication_coverage_accepted':True,'publication_accepted':True,'acceptance_gaps':[],'unresolved_required_publication_dependencies':[]})
        p['evidence_sha256_before']=p['evidence_sha256_after']=files(self.root);self.proof.write_bytes(encoded(p))
        return package.reader('originals-flagstaff-html-v1')(self.root,p,f)
    def report(self,p):return json.loads(artifacts(p)['validation-report.json'])
    def test_qualified_selected_true_strict_gates_exit_unchanged(self):
        p=self.qualify();r=self.report(p);self.assertTrue(r['selected_publication_ready']);self.assertFalse(r['complete']);self.assertFalse(r['downstream_ready']);self.assertEqual(r['status'],'incomplete');self.assertFalse(r['selected_publication_readiness']['independent_legal_review_inferred']);self.assertFalse(r['selected_publication_readiness']['jurisdiction_readiness_inferred'])
        self.assertEqual(sum(x['full_text'].count('[IMAGE]') for x in p.rows),2)
        out=self.base/'package';v=package.run(self.root,self.proof,self.family,out,'originals-flagstaff-html-v1');self.assertTrue(v['package_verified']);self.assertTrue(v['selected_publication_ready']);self.assertFalse(v['complete']);self.assertTrue(load(out/'run-manifest.json')['selected_publication_ready'])
        self.assertEqual(package.main(['verify','--out',str(out)]),2)
    def test_historical_unaccepted_source_stays_false(self):
        p=package.reader('originals-flagstaff-html-v1')(self.root,load(self.proof),load(self.family));r=self.report(p);self.assertFalse(r['selected_publication_ready']);self.assertFalse(r['complete']);self.assertFalse(p.inherited_coverage['source_consistency_complete'])
    def test_each_missing_false_or_string_gate_fails_closed(self):
        p=self.qualify()
        for gate in GATES:
            for value in [None,False,'true',1]:
                q=copy.deepcopy(p);q.readiness_evidence['gates'][gate]=value
                with self.subTest(gate=gate,value=value):self.assertFalse(self.report(q)['selected_publication_ready'])
    def test_named_structure_and_required_dependency_evidence_not_inferred(self):
        self.qualify();proof=load(self.proof);family=load(self.family);cov=load(self.root/'coverage.json');version={'snapshot':'fixture'}
        for key in ['legal_structure_qualified','required_nonimage_documents_complete','unresolved_required_publication_dependencies']:
            q=copy.deepcopy(proof);q['acceptance'].pop(key);e=common_publication_evidence(q,family,cov['config'],version,cov,file_hash(self.root/'coverage.json'))
            r=evaluate(e,PUBLICATION,cov['config'],version,cov,[])
            with self.subTest(key=key):self.assertFalse(r['ready'])
    def test_wrong_configuration_version_coverage_or_receipt_binding_refused(self):
        p=self.qualify()
        for key in p.readiness_evidence['binding']:
            q=copy.deepcopy(p);q.readiness_evidence['binding'][key]='0'*(64 if key in ['configuration_sha256','source_version_sha256','inherited_coverage_sha256'] else 63)
            with self.subTest(key=key):self.assertFalse(self.report(q)['selected_publication_ready'])
    def test_other_publishers_and_other_flagstaff_publication_unqualified(self):
        p=self.qualify()
        for publication in ['60-primary','67-lincoln-charter','original-flagstaff-az-secondary']:
            q=copy.deepcopy(p);q.publication_id=publication;q.readiness_evidence['publication_id']=publication
            with self.subTest(publication=publication):self.assertFalse(evaluate(q.readiness_evidence,q.publication_id,q.metadata['source_config'],q.metadata['source_version'],q.inherited_coverage,q.dispositions)['ready'])
        for mode in ['municode','encodeplus']:
            q=copy.deepcopy(p);q.readiness_evidence=None
            self.assertEqual(self.report(q)['selected_publication_readiness']['reasons'],['reader_has_no_qualified_readiness_evidence'])
    def test_unresolved_disposition_and_inferred_legal_review_block(self):
        p=self.qualify();p.dispositions[0]['disposition']='unresolved';self.assertFalse(self.report(p)['selected_publication_ready'])
        p=self.qualify();p.readiness_evidence['independent_legal_review_inferred']=True;self.assertFalse(self.report(p)['selected_publication_ready'])
    def test_images_and_metadata_payloads_still_refused(self):
        p=self.qualify();p.readiness_evidence['fault']={'images':[{'url':'DATA:application/octet-stream;base64,PIXELS'}]}
        with self.assertRaises(ValueError):self.report(p)
    def test_empty_link_ledger_cannot_replace_legal_structure_proof(self):
        p=self.qualify();p.readiness_evidence['gates']['legal_structure_qualified']=False;p.inherited_coverage['unresolved_dependencies']=[]
        self.assertFalse(self.report(p)['selected_publication_ready'])

if __name__=='__main__':unittest.main()
