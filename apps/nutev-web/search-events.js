const nativeFetch=window.fetch.bind(window);
const RETRYABLE_JOB_STATUS=new Set([408,429,500,502,503,504]);
const RETRY_DELAYS=[400,900,1800];

let lastResult=null;
let lastJob=null;
let lastHistory=[];

const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const emit=(name,detail)=>window.dispatchEvent(new CustomEvent(name,{detail}));

function requestMeta(input,init={}){
  try{
    const url=new URL(typeof input==='string'?input:input?.url||'',location.href);
    return {path:url.pathname,method:String(init?.method||input?.method||'GET').toUpperCase()};
  }catch{return{path:'',method:'GET'}}
}

function resultFromPayload(payload){
  if(payload?.result?.results)return payload.result;
  if(payload?.results)return payload;
  return null;
}

async function robustJobFetch(args,path){
  let lastError=null;
  for(let attempt=0;attempt<=RETRY_DELAYS.length;attempt+=1){
    try{
      const response=await nativeFetch(...args);
      if(response.ok||!RETRYABLE_JOB_STATUS.has(response.status)||attempt===RETRY_DELAYS.length)return response;
    }catch(error){
      lastError=error;
      if(attempt===RETRY_DELAYS.length)throw error;
    }
    const delay=RETRY_DELAYS[attempt];
    emit('nutev:search-transport-retry',{path,attempt:attempt+1,delay});
    await sleep(delay);
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
  emit('nutev:search-history',{searches:lastHistory,scope});
}
function processPayload(payload,{path,method}){
  if(path==='/api/searches'&&method==='GET'&&Array.isArray(payload?.searches)){
    publishHistory(payload.searches,payload.scope||'');return;
  }
  if(path==='/api/search/jobs'&&method==='POST'){
    publishJob(payload,'submission');return;
  }
  if(path.startsWith('/api/search/jobs/')){
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

window.NutEVSearchEvents={
  getLastResult:()=>lastResult,
  getLastJob:()=>lastJob,
  getLastHistory:()=>[...lastHistory],
  retryDelays:[...RETRY_DELAYS],
};
