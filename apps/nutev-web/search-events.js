import'./search-monitoring-ui.js';
import'./search-fulltext-ui.js';

const nativeFetch=window.fetch.bind(window);
const RETRYABLE_JOB_STATUS=new Set([408,429,500,502,503,504]);
const RETRY_DELAYS=[400,900,1800];
const MONITORING_ABANDONED_SENTINEL='__NUTEV_MONITORING_ABANDONED__';
const MAX_ABANDONED_JOBS=50;

let lastResult=null;
let lastJob=null;
let lastHistory=[];
let lastHistoryScope='';
const abandonedJobs=new Set();

const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const emit=(name,detail)=>window.dispatchEvent(new CustomEvent(name,{detail}));

function requestMeta(input,init={}){
  try{
    const url=new URL(typeof input==='string'?input:input?.url||'',location.href);
    return {path:url.pathname,method:String(init?.method||input?.method||'GET').toUpperCase()};
  }catch{return{path:'',method:'GET'}}
}

function jobIdFromPath(path){
  if(!String(path||'').startsWith('/api/search/jobs/'))return'';
  try{return decodeURIComponent(String(path).slice('/api/search/jobs/'.length)).trim()}catch{return''}
}

function resultFromPayload(payload){
  if(payload?.result?.results)return payload.result;
  if(payload?.results)return payload;
  return null;
}

function abandonedResponse(jobId){
  return new Response(JSON.stringify({
    error:'search_monitoring_abandoned',
    message:MONITORING_ABANDONED_SENTINEL,
    job_id:jobId,
  }),{
    status:409,
    headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'},
  });
}

function rememberAbandoned(jobId){
  if(!jobId)return;
  abandonedJobs.add(jobId);
  while(abandonedJobs.size>MAX_ABANDONED_JOBS){
    const oldest=abandonedJobs.values().next().value;
    if(!oldest)break;
    abandonedJobs.delete(oldest);
  }
}

async function robustJobFetch(args,path){
  const jobId=jobIdFromPath(path);
  if(jobId&&abandonedJobs.has(jobId))return abandonedResponse(jobId);
  let lastError=null;
  for(let attempt=0;attempt<=RETRY_DELAYS.length;attempt+=1){
    try{
      const response=await nativeFetch(...args);
      if(jobId&&abandonedJobs.has(jobId))return abandonedResponse(jobId);
      if(response.ok||!RETRYABLE_JOB_STATUS.has(response.status)||attempt===RETRY_DELAYS.length)return response;
    }catch(error){
      lastError=error;
      if(attempt===RETRY_DELAYS.length)throw error;
    }
    const delay=RETRY_DELAYS[attempt];
    emit('nutev:search-transport-retry',{path,attempt:attempt+1,delay});
    await sleep(delay);
    if(jobId&&abandonedJobs.has(jobId))return abandonedResponse(jobId);
  }
  throw lastError||new Error('Falha de conexão ao acompanhar a busca.');
}

function publishJob(job,source){
  lastJob=job;
  emit('nutev:search-job',{job,source});
}
function publishResult(result,source){
  lastResult=result;
  emit('nutev:search-result',{result,source});
}
function publishHistory(searches,scope=''){
  lastHistory=Array.isArray(searches)?searches:[];
  lastHistoryScope=String(scope||'');
  emit('nutev:search-history',{searches:lastHistory,scope:lastHistoryScope});
}
function processPayload(payload,{path,method}){
  if(path==='/api/searches'&&method==='GET'&&Array.isArray(payload?.searches)){
    publishHistory(payload.searches,payload.scope||'');return;
  }
  if(path==='/api/search/jobs'&&method==='POST'){
    const jobId=String(payload?.job_id||'').trim();
    if(jobId)abandonedJobs.delete(jobId);
    publishJob(payload,'submission');return;
  }
  if(path.startsWith('/api/search/jobs/')){
    const jobId=String(payload?.job_id||jobIdFromPath(path)).trim();
    if(jobId&&abandonedJobs.has(jobId))return;
    if(payload?.status==='queued'||payload?.status==='running'){publishJob(payload,'poll');return}
    if(payload?.status==='failed'){lastJob=payload;emit('nutev:search-failed',{job:payload,source:'poll'});return}
    if(payload?.status==='completed'){
      lastJob=payload;
      const result=resultFromPayload(payload);
      if(result)publishResult(result,'job');
      return;
    }
  }
  const result=resultFromPayload(payload);
  if(result)publishResult(result,path.startsWith('/api/searches/')?'history':'legacy');
}

function abandonJob(jobId=lastJob?.job_id){
  const id=String(jobId||'').trim();
  const currentId=String(lastJob?.job_id||'').trim();
  const currentStatus=String(lastJob?.status||'').trim();
  if(!id||id!==currentId||!['queued','running'].includes(currentStatus))return false;
  rememberAbandoned(id);
  emit('nutev:search-monitoring-abandoned',{job_id:id,job:lastJob});
  return true;
}

window.fetch=async(...args)=>{
  const meta=requestMeta(args[0],args[1]);
  const isJobRead=meta.method==='GET'&&meta.path.startsWith('/api/search/jobs/');
  const response=isJobRead?await robustJobFetch(args,meta.path):await nativeFetch(...args);
  const relevant=meta.path==='/api/search'||meta.path==='/api/searches'||meta.path==='/api/search/jobs'||isJobRead||meta.path.startsWith('/api/searches/');
  if(response.ok&&relevant){
    response.clone().json().then(payload=>processPayload(payload,meta)).catch(()=>{});
  }
  return response;
};

async function loadHistoryScope(scope='workspace',limit=50){
  const requested=scope==='project'?'project':'workspace';
  const safeLimit=Math.max(1,Math.min(Number(limit)||50,200));
  const response=await window.fetch(`/api/searches?limit=${safeLimit}&scope=${requested}`,{
    cache:'no-store',
    credentials:'same-origin',
  });
  if(!response.ok){
    const error=new Error(`history_http_${response.status}`);
    error.status=response.status;
    throw error;
  }
  return response;
}

window.NutEVSearchEvents={
  getLastResult:()=>lastResult,
  getLastJob:()=>lastJob,
  getLastHistory:()=>[...lastHistory],
  getLastHistoryScope:()=>lastHistoryScope,
  loadHistoryScope,
  isMonitoringAbandoned:jobId=>abandonedJobs.has(String(jobId||'').trim()),
  abandonJob,
  retryDelays:[...RETRY_DELAYS],
  monitoringAbandonedSentinel:MONITORING_ABANDONED_SENTINEL,
};