/* Shared QA bridge: exact reviewed Python inert-template JS, body-source slicing before attachment. */
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{spawnSync}=require('child_process');
const sourcePath=path.join(__dirname,'inert_browser_source.py'),source=fs.readFileSync(sourcePath,'utf8');
const match=/^JS = r'''([\s\S]*?)'''/m.exec(source);if(!match)throw Error('Reviewed inert source JS missing');
// Compile only the trusted, hash-recorded repository helper, never publisher raw HTML.
const JS=match[1],sanitize=eval('('+JS+')'),sha=v=>crypto.createHash('sha256').update(v).digest('hex');
async function attachInert(page,raw){
 const code="import importlib.util,sys;spec=importlib.util.spec_from_file_location('qa_inert_bridge',sys.argv[1]);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);sys.stdout.write(m.body_markup(sys.stdin.read()))";
 const sliced=spawnSync(process.env.PYTHON||process.env.PYTHON_BIN||'python3',['-B','-c',code,sourcePath],{input:raw,encoding:'utf8',maxBuffer:64*1024*1024});
 if(sliced.error||sliced.status!==0)throw Error('Inert source body preparation failed: '+(sliced.error||sliced.stderr));
 return page.evaluate(sanitize,sliced.stdout);
}
const provenance=()=>({helper_cjs_sha256:sha(fs.readFileSync(__filename)),helper_python_sha256:sha(fs.readFileSync(sourcePath)),evaluated_template_js_sha256:sha(JS),preparation:'body-source-template-inert-before-attachment-v2',all_network_blocked:true,no_image_decode_render_extraction_or_OCR:true});
module.exports={attachInert,provenance};
