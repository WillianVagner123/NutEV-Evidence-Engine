"use strict";
const fs=require("node:fs"), vm=require("node:vm"), assert=require("node:assert/strict");
const elements=new Map([["#status",{textContent:"private fixture"}]]);
const body={inert:false,replaceChildren(){elements.clear()}};
const document={body,documentElement:{style:{}},visibilityState:"visible",addEventListener(){},querySelector:s=>elements.get(s)||null};
let channel;
class BroadcastChannel {constructor(){channel=this}addEventListener(name,fn){this.listener=fn}postMessage(){}}
const location={href:"http://fixture.local/",origin:"http://fixture.local",replace(url){this.target=url},reload(){this.target="reload"}};
const payload=url=>url==='/api/auth/status'?{mode:'pilot'}:url==='/api/auth/me'?{user:{id:'U'}}:url==='/api/context'?{current:{workspace_id:'W',project_id:'P'}}:{entries:[]};
const nativeFetch=async input=>new Response(JSON.stringify(payload(String(input))),{status:200,headers:{'Content-Type':'application/json'}});
const window={fetch:nativeFetch,addEventListener(){},NutEVContext:{private:true}};
const context=vm.createContext({window,document,location,BroadcastChannel,URL,Headers,Request,Response,crypto:require('node:crypto').webcrypto,localStorage:{setItem(){}},setInterval(){},console});
(async()=>{
  vm.runInContext(fs.readFileSync('apps/nutev-web/tenant-session.js','utf8'),context);
  const response=await window.fetch('/api/library');
  channel.listener({data:'logout:fixture'});
  assert.equal(document.documentElement.style.visibility,'hidden');
  assert.equal(body.inert,true);
  assert.equal(window.NutEVContext,null);
  assert.equal(location.target,'/login.html');
  // An already-issued response must not paint, but its catch/finally may update
  // status controls until navigation commits. Do not swallow that page error.
  await assert.rejects(response.json(),/stale_response/);
  document.querySelector('#status').textContent='session ended';
  await assert.rejects(window.fetch('/api/library'),/context_invalidated/);
  assert.equal(document.documentElement.style.visibility,'hidden');
  assert.equal(body.inert,true);
  console.log('PASS: retired DOM remains hidden/inert, pending handlers safe, stale data rejected');
})().catch(error=>{console.error(error);process.exitCode=1});
