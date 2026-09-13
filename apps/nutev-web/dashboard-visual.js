const VISUAL_FILTER_CONTROLS={route:'filterRoute',source_provider:'filterProvider',year:'filterYear',full_text_status:'filterFullText'};
const VISUAL_PROVIDER_LABELS={pubmed:'PubMed',europepmc:'Europe PMC',europe_pmc:'Europe PMC',openalex:'OpenAlex',crossref:'Crossref',doaj:'DOAJ',semantic_scholar:'Semantic Scholar',lilacs_bvs:'LILACS / BVS',lilacs_bvs_native:'LILACS / BVS',scielo:'SciELO',scielo_native:'SciELO',scopus:'Scopus',wos:'Web of Science'};
const VISUAL_FULLTEXT_LABELS={retrieved:'Retrieved',partial:'Partial',unavailable:'Unavailable',not_retrieved:'Not retrieved',not_attempted:'Not attempted',unknown:'Unknown'};
const visualState={articles:[]};
const q=selector=>document.querySelector(selector);
const escapeHtml=value=>String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');
const formatNumber=value=>new Intl.NumberFormat('pt-BR').format(Number(value||0));
const formatPercent=(value,total)=>total?`${(100*Number(value||0)/Number(total)).toLocaleString('pt-BR',{maximumFractionDigits:1})}%`:'—';

function ensureStyles(){
  if(document.querySelector('link[data-dashboard-visual]'))return;
  const link=document.createElement('link');
  link.rel='stylesheet';
  link.href='./dashboard-visual.css';
  link.dataset.dashboardVisual='true';
  document.head.append(link);
}

function effectiveClass(row){return row.review_profile?.primary_document_class||row.document_class||'unclassified'}
function domains(row){return row.review_profile?.operational_domains||[]}
function routes(row){return row.routes||[]}
function countBy(rows,getter){const result={};for(const row of rows){const key=getter(row);if(!key)continue;result[key]=(result[key]||0)+1}return result}
function sortedEntries(counts){return Object.entries(counts).sort((a,b)=>b[1]-a[1]||String(a[0]).localeCompare(String(b[0])))}
function currentFilters(){
  const params=new URLSearchParams(location.search);
  return {
    route:params.get('route')||'',
    document_class:params.get('document_class')||'',
    domain:params.get('domain')||'',
    source_provider:params.get('source_provider')||'',
    year:params.get('year')||'',
    full_text_status:params.get('full_text_status')||''
  };
}
function filteredArticles(){
  const f=currentFilters();
  return visualState.articles.filter(row=>{
    if(f.route&&!routes(row).includes(f.route))return false;
    if(f.document_class&&effectiveClass(row)!==f.document_class)return false;
    if(f.domain&&!domains(row).includes(f.domain))return false;
    if(f.source_provider&&String(row.source_provider||'')!==f.source_provider)return false;
    if(f.year&&String(row.year||'')!==f.year)return false;
    if(f.full_text_status&&String(row.full_text_status||'unknown')!==f.full_text_status)return false;
    return true;
  });
}
function setDashboardFilter(key,value){
  const id=VISUAL_FILTER_CONTROLS[key];
  const select=id?q(`#${id}`):null;
  if(!select)return;
  select.value=select.value===String(value)?'':String(value);
  select.dispatchEvent(new Event('change',{bubbles:true}));
}
function corpusHref(){
  const f=currentFilters();
  const params=new URLSearchParams();
  if(f.document_class)params.set('document_class',f.document_class);
  if(f.source_provider)params.set('source_provider',f.source_provider);
  if(f.full_text_status)params.set('full_text_status',f.full_text_status);
  return `/articles.html${params.toString()?`?${params}`:''}`;
}

function injectVisualPanel(){
  if(q('#visualExploration'))return;
  const anchor=q('#dashboardFilters');
  if(!anchor)return;
  anchor.insertAdjacentHTML('afterend',`<section id="visualExploration" class="card visual-exploration" aria-label="Exploração visual do recorte atual">
    <div class="visual-head">
      <div><span class="visual-eyebrow">VISUAL EXPLORATION</span><h2>Leitura rápida do recorte</h2><p>Clique em uma barra ou segmento para cruzar filtros no próprio dashboard. Distribuição e volume não representam qualidade, certeza ou força da evidência.</p></div>
      <a id="visualCorpusLink" class="visual-open" href="/articles.html">Abrir recorte no Corpus ↗</a>
    </div>
    <div id="visualStats" class="visual-stats" aria-live="polite"></div>
    <div class="visual-grid">
      <article class="visual-panel visual-span-5"><div class="visual-panel-head"><div><strong>Full-text mix</strong><span>Status técnico do recorte</span></div></div><div id="visualFullText" class="segment-chart"></div></article>
      <article class="visual-panel visual-span-7"><div class="visual-panel-head"><div><strong>Provider mix</strong><span>Participação por fonte no recorte</span></div></div><div id="visualProviders" class="visual-bars"></div></article>
      <article class="visual-panel visual-span-4"><div class="visual-panel-head"><div><strong>Review routes</strong><span>Rotas operacionais podem se sobrepor</span></div></div><div id="visualRoutes" class="route-tiles"></div></article>
      <article class="visual-panel visual-span-8"><div class="visual-panel-head"><div><strong>Publication pulse</strong><span>Clique em um ano para filtrar; volume não implica tendência causal</span></div></div><div id="visualTimeline" class="pulse-chart"></div><div id="visualTimelineAxis" class="pulse-axis"></div></article>
    </div>
    <div class="visual-boundary">Cross-filter é apenas navegação analítica sobre o Tier A verificado. Nenhum clique altera Review, elegibilidade, inclusão, risco de viés, PRESS, GF-10 ou PRISMA.</div>
  </section>`);
}

function renderStats(rows){
  const total=visualState.articles.length;
  const providers=new Set(rows.map(row=>row.source_provider).filter(Boolean)).size;
  const years=rows.map(row=>Number(row.year)).filter(year=>year>=1900&&year<=2100).sort((a,b)=>a-b);
  const full=row=>String(row.full_text_status||'unknown');
  const available=rows.filter(row=>['retrieved','partial'].includes(full(row))).length;
  const yearText=years.length?(years[0]===years.at(-1)?String(years[0]):`${years[0]}–${years.at(-1)}`):'—';
  q('#visualStats').innerHTML=[
    ['Documentos',formatNumber(rows.length),`${formatPercent(rows.length,total)} do Tier A`],
    ['Providers',formatNumber(providers),'fontes presentes'],
    ['Janela temporal',yearText,years.length?'anos com data no recorte':'sem ano disponível'],
    ['Full text',formatPercent(available,rows.length),`${formatNumber(available)} retrieved + partial`]
  ].map(([label,value,note])=>`<div class="visual-stat"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong><small>${escapeHtml(note)}</small></div>`).join('');
}

function renderFullText(rows){
  const counts=countBy(rows,row=>row.full_text_status||'unknown');
  const entries=sortedEntries(counts);
  const total=Math.max(1,rows.length);
  const active=currentFilters().full_text_status;
  const node=q('#visualFullText');
  if(!entries.length){node.innerHTML='<div class="visual-empty">Sem documentos no recorte.</div>';return}
  node.innerHTML=`<div class="segment-track" role="group" aria-label="Distribuição de full text">${entries.map(([key,value])=>`<button type="button" class="segment${active===key?' active':''}" style="--segment-share:${100*value/total}%" data-visual-filter="full_text_status" data-visual-value="${escapeHtml(key)}" title="${escapeHtml(VISUAL_FULLTEXT_LABELS[key]||key)}: ${formatNumber(value)} (${formatPercent(value,rows.length)}). Clique para filtrar."><span class="sr-only">${escapeHtml(VISUAL_FULLTEXT_LABELS[key]||key)}: ${formatNumber(value)}</span></button>`).join('')}</div><div class="segment-legend">${entries.map(([key,value])=>`<button type="button" class="segment-legend-item${active===key?' active':''}" data-visual-filter="full_text_status" data-visual-value="${escapeHtml(key)}"><i aria-hidden="true"></i><span>${escapeHtml(VISUAL_FULLTEXT_LABELS[key]||key)}</span><strong>${formatNumber(value)}</strong><small>${formatPercent(value,rows.length)}</small></button>`).join('')}</div>`;
}

function renderProviders(rows){
  const entries=sortedEntries(countBy(rows,row=>row.source_provider||'unknown')).slice(0,7);
  const max=Math.max(1,...entries.map(([,value])=>Number(value||0)));
  const active=currentFilters().source_provider;
  q('#visualProviders').innerHTML=entries.length?entries.map(([key,value])=>`<button type="button" class="visual-bar${active===key?' active':''}" data-visual-filter="source_provider" data-visual-value="${escapeHtml(key)}" title="${escapeHtml(VISUAL_PROVIDER_LABELS[key]||key)}: ${formatNumber(value)} documentos. Clique para filtrar."><span class="visual-bar-label">${escapeHtml(VISUAL_PROVIDER_LABELS[key]||key)}</span><span class="visual-bar-track"><span style="width:${Math.max(2,100*value/max)}%"></span></span><strong>${formatNumber(value)}</strong><small>${formatPercent(value,rows.length)}</small></button>`).join(''):'<div class="visual-empty">Sem providers no recorte.</div>';
}

function renderRoutes(rows){
  const active=currentFilters().route;
  const data=[['B-NORM',rows.filter(row=>routes(row).includes('B-NORM')).length],['C-STRUCT',rows.filter(row=>routes(row).includes('C-STRUCT')).length]];
  const overlap=rows.filter(row=>routes(row).includes('B-NORM')&&routes(row).includes('C-STRUCT')).length;
  q('#visualRoutes').innerHTML=`${data.map(([key,value])=>`<button type="button" class="route-tile${active===key?' active':''}" data-visual-filter="route" data-visual-value="${key}"><span>${key}</span><strong>${formatNumber(value)}</strong><small>${formatPercent(value,rows.length)} do recorte</small></button>`).join('')}<div class="route-overlap-note"><strong>${formatNumber(overlap)}</strong><span>em overlap</span></div>`;
}

function renderTimeline(rows){
  const entries=Object.entries(countBy(rows,row=>{const year=Number(row.year);return year>=1900&&year<=2100?String(year):''})).map(([year,value])=>[Number(year),value]).sort((a,b)=>a[0]-b[0]);
  const node=q('#visualTimeline'),axis=q('#visualTimelineAxis');
  if(!entries.length){node.innerHTML='<div class="visual-empty">Ano de publicação indisponível neste recorte.</div>';axis.innerHTML='';return}
  const max=Math.max(...entries.map(([,value])=>value));
  const active=currentFilters().year;
  node.innerHTML=entries.map(([year,value])=>`<button type="button" class="pulse-bar${active===String(year)?' active':''}" style="height:${Math.max(5,100*value/max)}%" data-visual-filter="year" data-visual-value="${year}" title="${year}: ${formatNumber(value)} documentos (${formatPercent(value,rows.length)}). Clique para filtrar."><span class="sr-only">${year}: ${formatNumber(value)} documentos</span></button>`).join('');
  axis.innerHTML=`<span>${entries[0][0]}</span><span>${entries[Math.floor(entries.length/2)][0]}</span><span>${entries.at(-1)[0]}</span>`;
}

function renderVisualExploration(){
  if(!q('#visualExploration'))return;
  const rows=filteredArticles();
  renderStats(rows);renderFullText(rows);renderProviders(rows);renderRoutes(rows);renderTimeline(rows);
  const link=q('#visualCorpusLink');if(link)link.href=corpusHref();
}

function bindVisualEvents(){
  q('#visualExploration')?.addEventListener('click',event=>{
    const control=event.target.closest('[data-visual-filter]');
    if(!control)return;
    setDashboardFilter(control.dataset.visualFilter,control.dataset.visualValue);
  });
  document.addEventListener('change',event=>{
    if(event.target.closest('#dashboardFilters'))setTimeout(renderVisualExploration,0);
  });
  q('#clearDashboardFilters')?.addEventListener('click',()=>setTimeout(renderVisualExploration,0));
  window.addEventListener('popstate',()=>setTimeout(renderVisualExploration,0));
}

async function waitForFilters(){
  for(let attempt=0;attempt<100;attempt+=1){if(q('#dashboardFilters'))return true;await new Promise(resolve=>setTimeout(resolve,75))}
  return false;
}

async function initVisualExploration(){
  ensureStyles();
  if(!await waitForFilters())return;
  try{
    const response=await fetch('/agent-context/article1/ARTICLE_SUMMARIES.jsonl',{cache:'no-store'});
    if(!response.ok)throw new Error(`HTTP ${response.status}`);
    visualState.articles=(await response.text()).split(/\r?\n/).filter(Boolean).map(JSON.parse);
    injectVisualPanel();bindVisualEvents();renderVisualExploration();
  }catch(error){
    const anchor=q('#dashboardFilters');
    anchor?.insertAdjacentHTML('afterend',`<section class="card visual-exploration"><div class="visual-empty">Exploração visual indisponível: ${escapeHtml(error.message)}</div></section>`);
  }
}

initVisualExploration();
