'use strict';
const vm=require('node:vm'), fs=require('node:fs'), assert=require('node:assert/strict');
const nodes=new Map();
function node(selector){
  if(!nodes.has(selector))nodes.set(selector,{
    value:selector==='#libraryScope'?'workspace':'',disabled:false,textContent:'',innerHTML:'',
    classList:{add(){},remove(){},toggle(){}},addEventListener(type,fn){this[type]=fn},
    querySelector(){return{disabled:false}},querySelectorAll(){return[]}
  });
  return nodes.get(selector);
}
const pending=[];let historyWrites=0;
const response=payload=>({ok:true,json:async()=>payload});
const context=vm.createContext({console,URL,URLSearchParams,Date,setTimeout,
  location:{href:'http://fixture.local/evidence-library.html',search:''},
  history:{replaceState(){historyWrites++}},
  document:{querySelector:node},
  fetch:async url=>{
    if(url==='/api/auth/status')return new Promise(()=>{}); // initialization still in flight
    if(url.startsWith('/api/library?'))return new Promise(resolve=>pending.push(resolve));
    throw new Error('unexpected network request '+url);
  }
});
(async()=>{
  vm.runInContext(fs.readFileSync('apps/nutev-web/evidence-library-page.js','utf8'),context);
  assert.equal(node('#libraryScope').disabled,true,'scope must be disabled before trusted context loads');
  assert.equal(node('#saveLibraryPlacement').disabled,true,'save must be disabled before context loads');
  node('#libraryScope').value='project';
  node('#libraryScope').change();
  assert.equal(historyWrites,0,'early events must not rewrite project intent as workspace');
  vm.runInContext("contextPayload={current:{workspace_id:'W',project_id:'P'},workspaces:[],projects:[]};setContextReady(true)",context);
  const older=vm.runInContext('loadLibrary()',context);
  const newer=vm.runInContext('loadLibrary()',context);
  assert.equal(pending.length,2);
  const entry=note=>({document:{title:note},placement:{notes:note,state:'not_screened'}});
  pending[1](response({entries:[entry('LATEST_PRIVATE_PROJECT')]}));await newer;
  const expected=node('#libraryEntries').innerHTML;
  assert.match(expected,/LATEST_PRIVATE_PROJECT/);
  pending[0](response({entries:[entry('OLD_WORKSPACE_RESPONSE')]}));await older;
  assert.equal(node('#libraryEntries').innerHTML,expected,'old scope response must not repaint newer view');
  console.log('PASS: initialization guarded, explicit scope preserved, stale library response rejected');
})().catch(error=>{console.error(error);process.exitCode=1});
