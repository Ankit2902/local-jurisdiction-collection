import assert from 'node:assert/strict';
import {validateJob,validateDownloadUrl} from './transport_guards.mjs';
const job={section_url:'https://everett.municipal.codes/EMC/1.01.010',share_url:'https://everett.municipal.codes/EMC/1.01.010/share',export_url:'https://everett.municipal.codes/EMC/1.01.010/export.html?download=true',expected_id:'1.01.010'};
assert.doesNotThrow(()=>validateJob(job));assert.doesNotThrow(()=>validateDownloadUrl(job.export_url,job));assert.doesNotThrow(()=>validateDownloadUrl('blob:https://everett.municipal.codes/9d034d25-cfde-457a-aa2a-35a3854f5a4f',job));
for(const bad of ['blob:https://attacker.example/abc','https://attacker.example/download.html','https://everett.municipal.codes/Charter/1/export.html?download=true','data:text/html,test'])assert.throws(()=>validateDownloadUrl(bad,job));
for(const bad of [{...job,export_url:'https://everett.municipal.codes/EMC/1.01.020/export.html?download=true'},{...job,share_url:'https://attacker.example/share'},{...job,section_url:'http://everett.municipal.codes/EMC/1.01.010'}])assert.throws(()=>validateJob(bad));
console.log('10 transport scope/blob guard cases passed');
