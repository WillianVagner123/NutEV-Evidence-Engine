import'./saved-library.js';

const legacy=window.NutEVSavedLibrary;
const CHANGE_EVENT='nutev:saved-library-changed';

function emit(detail={}){
  window.dispatchEvent(new CustomEvent(CHANGE_EVENT,{detail}));
}

async function authMode(){
  try{
    const response=await fetch('/api/auth/status',{cache:'no-store',credentials:'same-origin'});
    if(!response.ok)return'legacy';
    const payload=await response.json();
    return payload?.mode==='pilot'?'pilot':'legacy';
  }catch{return'legacy'}
}

async function serverContext(){
  const response=await fetch('/api/context',{cache:'no-store',credentials:'same-origin'});
  if(!response.ok)return null;
  const payload=await response.json();
  return payload?.current?.workspace_id?payload.current:null;
}

async function modeState(){
  const mode=await authMode();
  if(mode!=='pilot')return{mode:'legacy',context:null};
  return{mode:'pilot',context:await serverContext()};
}

function normalizedServerEntry(entry){
  const placement=entry?.placement||{};
  const document=entry?.document||{};
  return{
    id:String(placement.placement_id||''),
    placement_id:String(placement.placement_id||''),
    article_id:String(document.article_id||placement.article_id||''),
    title:String(document.title||'Artigo sem título'),
    year:document.year??null,
    journal:String(document.journal||''),
    doi:String(document.doi||''),
    pmid:String(document.pmid||''),
    pmcid:String(document.pmcid||''),
    abstract:String(document.abstract||''),
    state:String(placement.state||'not_screened'),
    tags:Array.isArray(placement.tags)?placement.tags:[],
    notes:String(placement.notes||''),
    saved_at:String(placement.updated_at||placement.created_at||''),
    project_id:placement.project_id||null,
    workspace_id:String(placement.workspace_id||''),
    raw:{...document,article_id:String(document.article_id||placement.article_id||'')},
    storage:'server_placement',
  };
}

async function serverList(context){
  if(!context)return[];
  const scope=context.project_id?'project':'workspace';
  const response=await fetch(`/api/library?scope=${scope}&limit=500`,{
    cache:'no-store',
    credentials:'same-origin',
  });
  if(!response.ok)throw new Error(`evidence_library_http_${response.status}`);
  const payload=await response.json();
  return(Array.isArray(payload?.entries)?payload.entries:[]).map(normalizedServerEntry);
}

function articleId(record){
  return String(record?.article_id||record?.raw?.article_id||'').trim();
}

const facade={
  ...legacy,
  changeEvent:CHANGE_EVENT,
  recordId(record){
    return articleId(record)||legacy.recordId(record);
  },
  async storageMode(){
    return(await modeState()).mode;
  },
  async list(){
    const state=await modeState();
    if(state.mode==='legacy')return legacy.list();
    return serverList(state.context);
  },
  async get(id){
    const state=await modeState();
    if(state.mode==='legacy')return legacy.get(id);
    const rows=await serverList(state.context);
    const key=String(id||'');
    return rows.find(row=>row.id===key||row.article_id===key)||null;
  },
  async isSaved(record){
    const state=await modeState();
    if(state.mode==='legacy')return legacy.isSaved(record);
    if(!state.context)return false;
    const wanted=articleId(record);
    if(!wanted)return false;
    return(await serverList(state.context)).some(row=>row.article_id===wanted);
  },
  async save(record){
    const state=await modeState();
    if(state.mode==='legacy')return legacy.save(record);
    if(!state.context)throw new Error('workspace_context_required');
    const id=articleId(record);
    if(!id)throw new Error('global_article_id_required');
    const scope=state.context.project_id?'project':'workspace';
    const response=await fetch('/api/library/placements',{
      method:'POST',
      credentials:'same-origin',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({article_id:id,scope,state:'not_screened',tags:[],notes:''}),
    });
    if(!response.ok)throw new Error(`evidence_library_save_${response.status}`);
    const saved=normalizedServerEntry(await response.json());
    emit({action:'save',id:saved.id,article_id:saved.article_id,storage:'server'});
    return saved;
  },
  async remove(id){
    const state=await modeState();
    if(state.mode==='legacy')return legacy.remove(id);
    if(!state.context)return false;
    const key=String(id||'');
    const row=(await serverList(state.context)).find(item=>item.id===key||item.article_id===key);
    if(!row)return false;
    const response=await fetch(`/api/library/placements/${encodeURIComponent(row.placement_id)}`,{
      method:'DELETE',
      credentials:'same-origin',
    });
    if(!response.ok)return false;
    emit({action:'remove',id:row.id,article_id:row.article_id,storage:'server'});
    return true;
  },
  async clear(){
    const state=await modeState();
    if(state.mode==='legacy')return legacy.clear();
    if(!state.context)return true;
    const rows=await serverList(state.context);
    for(const row of rows){
      const response=await fetch(`/api/library/placements/${encodeURIComponent(row.placement_id)}`,{
        method:'DELETE',
        credentials:'same-origin',
      });
      if(!response.ok)throw new Error(`evidence_library_clear_${response.status}`);
    }
    emit({action:'clear',storage:'server'});
    return true;
  },
  async exportJson(){
    const state=await modeState();
    if(state.mode==='legacy'&&typeof legacy.exportJson==='function')return legacy.exportJson();
    return JSON.stringify(await serverList(state.context),null,2);
  },
};

window.NutEVSavedLibrary=facade;
window.NutEVEvidenceLibrary=facade;
