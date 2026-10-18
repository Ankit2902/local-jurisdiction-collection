"""Final acquisition-only provenance and no-download inventory guards."""
import contextlib,io,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from source_common import load,save
from profile import load_config
import cli,workflow,flagstaff_inventory as inventory,shared_transport as transport
from test_operational import sources,ROOT
class ProtocolGuards(unittest.TestCase):
 def test_replay_metadata_cannot_be_relabelled_live(self):
  cfg=load_config(ROOT/'configs/king-county.json')
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);html,word=sources(root);out=root/'job';workflow.replay(cfg,html,out,word);s=load(out/'checkpoint.json');s['acquisition_mode']='live';save(out/'checkpoint.json',s)
   with patch('verify.verify',side_effect=AssertionError('parser must not start')):
    with self.assertRaisesRegex(ValueError,'provenance mode'):cli.verify(cfg,out=out)
 def test_body_and_text_coverage_do_not_collapse_into_edition_failure(self):
  cfg=load_config(ROOT/'configs/flagstaff.json');html={'complete':False,'source_documents':1,'acquired_parsed_documents':1,'source_blocks':3,'owned_blocks':3,'source_tables':0,'owned_tables':0,'source_graph_edges':1,'matched_toc_edges':1,'missing_toc_edges':0,'extra_body_headings':0,'heading_only_unresolved':0,'unresolved_nonimage_dependencies':0,'opening_closing_inventory_equal':True,'opening_closing_roots_equal':True,'opening_currency':'OpeningOrd1','closing_currency':'ClosingOrd2','errors':['source currency drift'],'source_text_ownership_complete':True,'full_primary_source_ownership_complete':True,'dependency_coverage_complete':True}
  r=workflow.coverage(cfg.binding(),Path('/unused'),html=html,write=False);self.assertTrue(r['publication_bodies_acquired_and_owned']);self.assertTrue(r['publication_text_complete']);self.assertTrue(r['legal_structure_qualified']);self.assertFalse(r['source_consistency_complete']);self.assertFalse(r['publication_accepted'])
 def test_counts_without_source_fidelity_proof_cannot_claim_body_or_structure(self):
  cfg=load_config(ROOT/'configs/flagstaff.json');html={'complete':True,'source_documents':1,'acquired_parsed_documents':1,'source_blocks':3,'owned_blocks':3,'source_tables':0,'owned_tables':0,'source_graph_edges':1,'matched_toc_edges':1,'missing_toc_edges':0,'extra_body_headings':0,'heading_only_unresolved':0,'unresolved_nonimage_dependencies':0,'opening_closing_inventory_equal':True,'opening_closing_roots_equal':True,'opening_currency':'SameOrd','closing_currency':'SameOrd','errors':[]}
  r=workflow.coverage(cfg.binding(),Path('/unused'),html=html,write=False);self.assertFalse(r['publication_bodies_acquired_and_owned']);self.assertFalse(r['publication_text_complete']);self.assertFalse(r['legal_structure_qualified']);self.assertFalse(r['publication_accepted'])
 def test_inventory_browser_disables_downloads_and_registers_no_saver(self):
  events=[];options={}
  class Page:
   def goto(self,*a,**kw):raise RuntimeError('Synthetic navigation stop before source request')
  class Context:
   def route(self,*a):pass
   def on(self,event,callback):events.append(event)
   def new_page(self):return Page()
   def close(self):pass
  class Browser:
   version='synthetic no-network browser'
   def new_context(self,**kw):options.update(kw);return Context()
   def close(self):pass
  class PW:
   def __init__(self):self.chromium=self
   def __enter__(self):return self
   def __exit__(self,*a):pass
   def launch(self,**kw):return Browser()
  with tempfile.TemporaryDirectory() as tmp,patch.object(inventory,'sync_playwright',return_value=PW()),patch.object(transport,'ROOT',Path(tmp)/'gate'):
   r=inventory.run(Path(tmp)/'inventory');self.assertIn('Synthetic navigation stop',r['error']['message']);self.assertFalse(options['accept_downloads']);self.assertNotIn('download',events);self.assertNotIn('page',events);self.assertFalse(list((Path(tmp)/'inventory').glob('download-*')))
if __name__=='__main__':unittest.main()
