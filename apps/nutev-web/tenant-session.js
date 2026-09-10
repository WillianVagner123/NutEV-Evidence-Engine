/* Browser context lease: constraints on server authorization, never credentials. */
(()=>{
  'use strict';
  const nativeFetch=window.fetch.bind(window);
  const epochKey='nutev-context-epoch'; // only a random invalidation signal, no private state
  const publicPaths=new Set(['/api/health','/api/version','/api/providers','/api/capabilities','/api/auth/status']);
  let lease=null,mode=null,invalid=false,boot=null;
  const channel=typeof BroadcastChannel==='function'?new BroadcastChannel(epochKey):null;
  const key=c=>JSON.stringify([c?.user||'',c?.workspace_id||'',c?.project_id||'']);
  function invalidate(login=false){
    if(invalid)return;
    invalid=true;
    document.documentElement.style.visibility='hidden';
    document.body?.replaceChildren();
    window.NutEVContext=null;
    if(login)location.replace('/login.html');else location.reload();
  }
  function announce(){
    const value=crypto.randomUUID();
    channel?.postMessage(value);
    try{localStorage.setItem(epochKey,value)}catch{}
  }
  async function snapshot(){
    const me=await nativeFetch('/api/auth/me',{cache:'no-store',credentials:'same-origin'});
    if(me.status===401)return null;
    if(!me.ok)throw new Error('session_unavailable');
    const ctx=await nativeFetch('/api/context',{cache:'no-store',credentials:'same-origin'});
    if(!ctx.ok)throw new Error('context_unavailable');
    const [user,context]=await Promise.all([me.json(),ctx.json()]);
    return{user:user.user.id,workspace_id:context.current?.workspace_id||'',project_id:context.current?.project_id||''};
  }
  function initialize(){
    if(!boot)boot=(async()=>{
      const status=await nativeFetch('/api/auth/status',{cache:'no-store',credentials:'same-origin'});
      if(!status.ok)throw new Error('runtime_unavailable');
      mode=(await status.json()).mode;
      if(!['pilot','legacy'].includes(mode))throw new Error('runtime_unknown');
      if(mode==='pilot')lease=await snapshot();
    })();
    return boot;
  }
  async function verifyLease(){
    try{
      await initialize();
      if(mode!=='pilot'||invalid)return;
      const now=await snapshot();
      if(key(now)!==key(lease))invalidate(!now);
    }catch{if(mode==='pilot')invalidate(true)}
  }
  window.fetch=async(input,options={})=>{
    const url=new URL(input instanceof Request?input.url:String(input),location.href);
    if(url.origin!==location.origin||!url.pathname.startsWith('/api/'))return nativeFetch(input,options);
    const path=url.pathname;
    if(publicPaths.has(path))return nativeFetch(input,options);
    await initialize();
    if(mode!=='pilot')return nativeFetch(input,options);
    if(invalid)throw new Error('context_invalidated');
    const mutation=['/api/context/select','/api/auth/logout','/api/auth/login'].includes(path);
    const guest=path.startsWith('/api/article1/d132/');
    const privateRequest=!path.startsWith('/api/auth/')&&path!=='/api/context'&&!guest;
    const headers=new Headers(options.headers||(input instanceof Request?input.headers:undefined));
    if(lease&&privateRequest){
      headers.set('X-NutEV-User',lease.user);
      headers.set('X-NutEV-Workspace',lease.workspace_id);
      headers.set('X-NutEV-Project',lease.project_id);
    }
    const response=await nativeFetch(input,{...options,headers,cache:'no-store',credentials:'same-origin'});
    if(mutation&&response.ok){announce();return response}
    if(response.status===401&&!guest&&!path.startsWith('/api/auth/')){
      invalidate(true);throw new Error('session_expired');
    }
    if(response.status===409&&response.headers.has('X-NutEV-User')){
      const actual={user:response.headers.get('X-NutEV-User'),workspace_id:response.headers.get('X-NutEV-Workspace'),project_id:response.headers.get('X-NutEV-Project')};
      if(key(actual)!==key(lease)){invalidate();throw new Error('stale_context')}
    }
    if(privateRequest&&response.ok){
      const now=await snapshot();
      if(key(now)!==key(lease)){invalidate(!now);throw new Error('stale_response_context')}
    }
    // Even already-issued responses must not paint an invalidated page.
    for(const method of ['json','text','blob','arrayBuffer']){
      const read=response[method].bind(response);
      response[method]=async()=>{const payload=await read();if(invalid)throw new Error('stale_response');return payload};
    }
    if(invalid)throw new Error('stale_response');
    return response;
  };
  channel?.addEventListener('message',()=>{if(mode==='pilot')invalidate()});
  window.addEventListener('storage',e=>{if(e.key===epochKey&&mode==='pilot')invalidate()});
  window.addEventListener('focus',verifyLease);
  document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')verifyLease()});
  window.addEventListener('pageshow',e=>{if(e.persisted)invalidate()});
  window.addEventListener('pagehide',()=>{if(mode==='pilot')document.documentElement.style.visibility='hidden'});
  // A short lease bounds visible stale content after administrator revocation.
  setInterval(()=>{if(document.visibilityState==='visible')verifyLease()},5000);
})();
