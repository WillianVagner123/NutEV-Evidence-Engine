'use strict';
const vm = require('node:vm');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const nodes = new Map();
const buttons = [{disabled: false}];
function node(selector) {
  if (!nodes.has(selector)) nodes.set(selector, {
    innerHTML: '', textContent: '', disabled: false,
    classList: {add(){}, remove(){}, toggle(){}},
    addEventListener(){}
  });
  return nodes.get(selector);
}
const auth = [];
let exportsRead = 0;
const response = body => ({ok: true, json: async()=>body});
const context = vm.createContext({
  console, Intl, Date,
  document: {querySelector: node, querySelectorAll: ()=>buttons},
  fetch: async url => {
    if (url === '/api/auth/status') return new Promise(resolve=>auth.push(resolve));
    if (url === '/api/context') return response({current:{project_id:'P',workspace_id:'W'},workspaces:[],projects:[]});
    if (url === '/api/exports') { exportsRead++; return response({exports:[{id:'latest-export',export_kind:'fixture'}]}); }
    if (url === '/api/audit?limit=50') return response({chain_valid:true,events:[]});
    throw new Error('unexpected URL '+url);
  }
});
(async()=>{
  vm.runInContext(fs.readFileSync('apps/nutev-web/exports-page.js','utf8'),context);
  assert.equal(auth.length,1);
  assert.equal(node('#refreshExports').disabled,true);
  assert.equal(buttons[0].disabled,true);
  const newer = vm.runInContext('loadAll()',context);
  assert.equal(auth.length,2);
  auth[1](response({mode:'pilot'}));
  await newer;
  assert.match(node('#exportList').innerHTML,/latest-export/);
  const completed = node('#exportList').innerHTML;
  assert.equal(node('#refreshExports').disabled,false);
  auth[0](response({mode:'pilot'}));
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(exportsRead,1,'superseded load must not fetch or repaint current exports');
  assert.equal(node('#exportList').innerHTML,completed);
  assert.equal(node('#refreshExports').disabled,false);
  console.log('PASS: stale loads rejected; controls locked during refresh; latest cards preserved');
})().catch(error=>{console.error(error);process.exitCode=1});
