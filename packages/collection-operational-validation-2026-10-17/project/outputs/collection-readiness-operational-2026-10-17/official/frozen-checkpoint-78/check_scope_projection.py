#!/usr/bin/env python3
"""Evaluate only exact changed aggregation AST values on retained parsed evidence.
This does not call/replace a verifier, reparse PDFs, or modify any old coverage.
"""
import argparse,ast,hashlib,json,pathlib
p=argparse.ArgumentParser();p.add_argument('--old-code',type=pathlib.Path,required=True);p.add_argument('--new-code',type=pathlib.Path,required=True);p.add_argument('--run',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def expressions(path):
 tree=ast.parse(path.read_text());f=next(f for f in tree.body if isinstance(f,ast.FunctionDef)and f.name=='reconcile');node=next(n.value for n in f.body if isinstance(n,ast.Return));return {k.value:v for k,v in zip(node.keys,node.values)}
old,new=expressions(a.old_code),expressions(a.new_code);changed=[k for k in old if ast.dump(old[k],include_attributes=False)!=ast.dump(new[k],include_attributes=False)];assert changed==['legal_semantic_coverage_complete','manual_review_required'],changed
run=a.run;report=json.loads((run/'coverage.json').read_text());state=json.loads((run/'checkpoint.json').read_text());records=[]
for item in state['items']:
 path=run/'items'/(hashlib.sha256(item['id'].encode()).hexdigest()[:24]+'.json');records+=json.loads(path.read_text())['records']
env={'body_complete':report['publication_html_text_coverage_complete'],'unresolved_assets':report['required_assets_unresolved'],'required_components':report['required_components_unresolved'],'native_text_complete':report['required_attachment_text_normalization_qualified'],'page_files':report['pdf_files'],'records':records};values={}
for k in changed:
 prior=eval(compile(ast.Expression(old[k]),'<exact-prior-reconcile-expression>','eval'),{},env);current=eval(compile(ast.Expression(new[k]),'<exact-candidate-reconcile-expression>','eval'),{},env);assert prior==report[k];values[k]={'historical72':prior,'current78_projection':current}
result={'schema':1,'scope':'Pure changed-expression AST projection on exact terminal retained parsed record evidence. Not full current-code replay or verifier pass; historical coverage remains unchanged.','publication_id':report['publication_identity']['id'],'terminal_coverage_sha256':sha(run/'coverage.json'),'checkpoint_sha256':sha(run/'checkpoint.json'),'records_sha256':sha(run/'records.jsonl'),'old_collect_sha256':sha(a.old_code),'new_collect_sha256':sha(a.new_code),'changed_reconcile_values':changed,'actual_values':values,'unresolved_required_occurrences':len(env['unresolved_assets']),'native_text_complete':env['native_text_complete'],'intentional_image_omissions':report['policy_omitted_image_count'],'historical_output_mutated':False,'pass':True};a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(values,indent=2))
