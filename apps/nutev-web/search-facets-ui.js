import{canonicalDocumentClass,documentClassLabel}from'./document-classes.js';

const RESULT_BATCH=100;
const PROVIDER_LABELS={
  pubmed:'PubMed',europepmc:'Europe PMC',openalex:'OpenAlex',crossref:'Crossref',doaj:'DOAJ',semantic_scholar:'Semantic Scholar',lilacs_bvs_native:'LILACS/BVS',scielo_native:'SciELO',
};
const CONFIDENCE_LABELS={high:'alta',medium:'média',low:'sinal insuficiente'};

let latestSearch=null;
let currentSearchKey='';
let visibleResults=RESULT_BATCH;
let textDebounce=0;
let filters={text:'',year:'',documentClass:'',provider:'',taxonomy:'',sort:'query_relevance'};

const $=selector=>document.querySelector(selector);
const esc=value=>String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');

function searchKey(data){return String(data?.search_id||`${data?.query||''}|${data?.created_at||''}|${data?.returned_records||0}`)}
function number(value,fallback=-Infinity){const parsed=Number(value);return Number.isFinite(parsed)?parsed:fallback}
function yearValue(record){const value=String(record?.year??'').trim();return /^\d{4}$/.test(value)?value:''}
function providerValues(record){
  const values=[];
  const primary=String(record?.source_provider||record?.source||'').trim();if(primary)values.push(primary);
  if(Array.isArray(record?.source_providers))for(const value of record.source_providers){const provider=String(value||'').trim();if(provider)values.push(provider)}
  return [...new Set(values)];
}
function providerValue(record){return providerValues(record)[0]||''}
function taxonomyValue(record){return String(record?.search_classification?.taxonomy_primary||record?.taxonomy_primary||'').trim()}
function taxonomyLabel(value){return String(value||'').split('.').filter(Boolean).slice(-2).join(' › ').replaceAll('_',' ')}
function providerLabel(value){return PROVIDER_LABELS[value]||value||'Fonte não informada'}
function normalizedText(value){return String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('pt-BR')}
function searchableText(record){return normalizedText([record?.title,record?.abstract,record?.journal,record?.authors,...providerValues(record).map(providerLabel),taxonomyLabel(taxonomyValue(record))].filter(Boolean).join(' '))}

function inferredClass(record){
  const explicit=record?.search_classification?.document_class;if(explicit)return canonicalDocumentClass(explicit);
  const structured=record?.document_type_applied;if(structured&&canonicalDocumentClass(structured)!=='unclassified')return canonicalDocumentClass(structured);
  const value=`${record?.article_type||''} ${structured||''} ${record?.title||''}`.toLocaleLowerCase();
  if(value.includes('systematic review')||value.includes('meta-analysis')||value.includes('meta analysis'))return'evidence_synthesis';
  if(value.includes('guideline')||value.includes('consensus statement')||value.includes('position statement'))return'guidance';
  if(value.includes('competency framework')||value.includes('curriculum framework')||value.includes('implementation framework')||value.includes('implementation evaluation')||value.includes('implementation study'))return'framework_implementation';
  if(value.includes('randomized')||value.includes('randomised'))return'primary_randomized';
  if(value.includes('cohort')||value.includes('cross-sectional')||value.includes('case-control'))return'primary_observational';
  if(value.includes('qualitative'))return'primary_qualitative';
  if(value.includes('review'))return'review';
  return'unclassified';
}

function blankFilters(){return{text:'',year:'',documentClass:'',provider:'',taxonomy:'',sort:'query_relevance'}}
function captureResult(result){
  if(!result?.results)return;
  const key=searchKey(result);
  if(key!==currentSearchKey){
    currentSearchKey=key;
    visibleResults=RESULT_BATCH;
    filters=blankFilters();
  }
  latestSearch=result;
  setTimeout(enhance,0);
}

window.addEventListener('nutev:search-result',event=>captureResult(event.detail?.result));

function countedOptions(records,getValue,getLabel){
  const counts=new Map();
  for(const record of records){const value=getValue(record);if(!value)continue;counts.set(value,(counts.get(value)||0)+1)}
  return [...counts.entries()].map(([value,count])=>({value,label:getLabel(value),count}));
}
function countedMultiOptions(records,getValues,getLabel){
  const counts=new Map();
  for(const record of records)for(const value of new Set(getValues(record)||[])){if(!value)continue;counts.set(value,(counts.get(value)||0)+1)}
  return [...counts.entries()].map(([value,count])=>({value,label:getLabel(value),count}));
}
function optionHtml(option){return `<option value="${esc(option.value)}">${esc(option.label)} (${option.count.toLocaleString('pt-BR')})</option>`}

function ensureWorkspace(){
  const summary=$('#summary');const results=$('#results');
  if(!summary||!results)return null;
  let workspace=$('#resultFacetWorkspace');
  if(!workspace){
    workspace=document.createElement('section');workspace.id='resultFacetWorkspace';workspace.className='result-facet-workspace card hidden';workspace.setAttribute('aria-label','Refinar resultados retornados');
    results.before(workspace);
  }
  return workspace;
}

function activeFilterDescriptors(){
  const items=[];
  if(filters.text)items.push({key:'text',label:`Texto: ${filters.text}`});
  if(filters.year)items.push({key:'year',label:`Ano: ${filters.year}`});
  if(filters.documentClass)items.push({key:'documentClass',label:`Classe: ${documentClassLabel(filters.documentClass)}`});
  if(filters.provider)items.push({key:'provider',label:`Fonte: ${providerLabel(filters.provider)}`});
  if(filters.taxonomy)items.push({key:'taxonomy',label:`Tema: ${taxonomyLabel(filters.taxonomy)}`});
  return items;
}
function renderActiveFilters(){
  const root=$('#activeResultFilters');if(!root)return;
  const items=activeFilterDescriptors();
  root.innerHTML=items.length?`<span>${items.length} ${items.length===1?'filtro ativo':'filtros ativos'}</span>${items.map(item=>`<button type="button" class="facet-chip" data-clear-filter="${esc(item.key)}">${esc(item.label)} <span aria-hidden="true">×</span></button>`).join('')}`:'<span>Nenhum filtro ativo.</span>';
  root.querySelectorAll('[data-clear-filter]').forEach(button=>button.addEventListener('click',()=>{
    const key=button.dataset.clearFilter;if(key&&Object.hasOwn(filters,key))filters[key]='';visibleResults=RESULT_BATCH;populateWorkspace();renderFilteredResults();
  }));
}

function populateWorkspace(){
  const workspace=ensureWorkspace();if(!workspace||!latestSearch)return;
  const records=latestSearch.results||[];
  const years=countedOptions(records,yearValue,value=>value).sort((a,b)=>Number(b.value)-Number(a.value));
  const classes=countedOptions(records,inferredClass,documentClassLabel).sort((a,b)=>a.label.localeCompare(b.label,'pt-BR'));
  const providers=countedMultiOptions(records,providerValues,providerLabel).sort((a,b)=>a.label.localeCompare(b.label,'pt-BR'));
  const taxonomies=countedOptions(records,taxonomyValue,taxonomyLabel).sort((a,b)=>b.count-a.count||a.label.localeCompare(b.label,'pt-BR'));
  workspace.dataset.searchKey=currentSearchKey;
  workspace.classList.remove('hidden');
  workspace.innerHTML=`<div class="facet-head"><div><strong>Refinar resultados</strong><span>Filtros aplicados somente aos ${records.length.toLocaleString('pt-BR')} resultados retornados nesta busca, sem refazer a busca nas fontes.</span></div><button id="clearResultFacets" type="button" class="ghost">Limpar filtros</button></div>
    <div class="facet-grid">
      <label class="facet-text-search">Buscar nestes resultados<input id="facetText" type="search" autocomplete="off" placeholder="Título, resumo, periódico ou tema"></label>
      <label>Ano<select id="facetYear"><option value="">Todos os anos</option>${years.map(optionHtml).join('')}</select></label>
      <label>Classe do artigo<select id="facetClass"><option value="">Todas as classes</option>${classes.map(optionHtml).join('')}</select></label>
      <label>Fonte<select id="facetProvider"><option value="">Todas as fontes</option>${providers.map(optionHtml).join('')}</select></label>
      <label>Tema / taxonomia<select id="facetTaxonomy"><option value="">Todos os temas</option>${taxonomies.map(optionHtml).join('')}</select></label>
      <label>Ordenar por<select id="facetSort"><option value="query_relevance">Relevância à consulta</option><option value="final_score">Ranking final NutEV</option><option value="newest">Mais recentes</option><option value="nutev_priority">Prioridade NutEV</option></select></label>
    </div>
    <div id="activeResultFilters" class="facet-active" aria-live="polite"></div>
    <div class="facet-foot"><strong id="facetResultCount">—</strong><span id="facetResultLabel">resultados após filtros</span><span class="facet-boundary">Um artigo deduplicado pode contar em mais de uma fonte quando houve múltiplas manifestações observadas. Isso é proveniência de recuperação, não qualidade da evidência.</span></div>`;
  $('#facetText').value=filters.text;
  $('#facetYear').value=filters.year;
  $('#facetClass').value=filters.documentClass;
  $('#facetProvider').value=filters.provider;
  $('#facetTaxonomy').value=filters.taxonomy;
  $('#facetSort').value=filters.sort;
  $('#facetText').addEventListener('input',event=>{
    filters.text=event.target.value.trim();visibleResults=RESULT_BATCH;clearTimeout(textDebounce);textDebounce=setTimeout(()=>{renderActiveFilters();renderFilteredResults()},140);
  });
  const bind=(id,key)=>$(id).addEventListener('change',event=>{filters[key]=event.target.value;visibleResults=RESULT_BATCH;renderActiveFilters();renderFilteredResults()});
  bind('#facetYear','year');bind('#facetClass','documentClass');bind('#facetProvider','provider');bind('#facetTaxonomy','taxonomy');bind('#facetSort','sort');
  $('#clearResultFacets').addEventListener('click',()=>{filters=blankFilters();visibleResults=RESULT_BATCH;populateWorkspace();renderFilteredResults()});
  renderActiveFilters();
}

function filteredEntries(){
  const records=latestSearch?.results||[];const needle=normalizedText(filters.text);
  const entries=records.map((record,index)=>({record,index})).filter(({record})=>{
    if(needle&&!searchableText(record).includes(needle))return false;
    if(filters.year&&yearValue(record)!==filters.year)return false;
    if(filters.documentClass&&inferredClass(record)!==filters.documentClass)return false;
    if(filters.provider&&!providerValues(record).includes(filters.provider))return false;
    if(filters.taxonomy&&taxonomyValue(record)!==filters.taxonomy)return false;
    return true;
  });
  const tie=(a,b)=>number(b.record.reference_score)-number(a.record.reference_score)||number(a.record.reference_rank,Number.MAX_SAFE_INTEGER)-number(b.record.reference_rank,Number.MAX_SAFE_INTEGER);
  entries.sort((a,b)=>{
    if(filters.sort==='newest')return number(b.record.year,0)-number(a.record.year,0)||tie(a,b);
    if(filters.sort==='nutev_priority')return number(b.record.nutev_priority_score)-number(a.record.nutev_priority_score)||number(b.record.query_relevance_score)-number(a.record.query_relevance_score)||tie(a,b);
    if(filters.sort==='final_score')return tie(a,b);
    return number(b.record.query_relevance_score)-number(a.record.query_relevance_score)||tie(a,b);
  });
  return entries;
}

function whyMatched(record){
  const classification=record.search_classification||{};const query=classification.query_match||{};const parts=[];
  if((query.title_hits||[]).length)parts.push(`título: ${(query.title_hits||[]).slice(0,5).join(', ')}`);
  if((query.abstract_hits||[]).length)parts.push(`resumo: ${(query.abstract_hits||[]).slice(0,5).join(', ')}`);
  const taxonomy=classification.taxonomy_primary||record.taxonomy_primary;if(taxonomy)parts.push(`tema: ${taxonomyLabel(taxonomy)}`);
  if(record.document_type_applied)parts.push(`sinal documental: ${record.document_type_applied}`);
  return parts;
}
function rankingSignals(record){
  const query=number(record.query_relevance_score,0),priority=number(record.nutev_priority_score,0);const parts=[];
  if(Number.isFinite(query))parts.push(`relevância para a consulta ${query.toFixed(1)}`);
  if(Number.isFinite(priority))parts.push(`prioridade NutEV ${priority.toFixed(1)}`);
  return parts;
}
function sourceManifestations(record){return Array.isArray(record?.source_manifestations)?record.source_manifestations.filter(item=>item&&typeof item==='object'):[]}
function provenanceDetails(record){
  const providers=providerValues(record);const manifestations=sourceManifestations(record);
  if(providers.length<2&&manifestations.length<2)return'';
  const rows=manifestations.slice(0,10).map(item=>{
    const provider=providerLabel(String(item.provider||item.source||''));
    const query=String(item.provider_query||'').trim();
    const ids=[item.pmid?`PMID ${item.pmid}`:'',item.doi?`DOI ${item.doi}`:''].filter(Boolean).join(' · ');
    return `<li><strong>${esc(provider)}</strong>${ids?`<span>${esc(ids)}</span>`:''}${query?`<code title="Query enviada à fonte">${esc(query.length>260?`${query.slice(0,260)}…`:query)}</code>`:''}</li>`;
  }).join('');
  return `<details class="retrieval-provenance"><summary>Origens da recuperação · ${providers.length.toLocaleString('pt-BR')} fontes</summary><p>Estas fontes recuperaram manifestações do mesmo artigo antes da deduplicação. Múltiplas fontes não aumentam qualidade, certeza ou elegibilidade científica.</p>${rows?`<ul>${rows}</ul>`:''}</details>`;
}

function resultCard(entry,viewPosition){
  const record=entry.record;const href=record.doi?`https://doi.org/${String(record.doi).replace(/^https?:\/\/doi\.org\//i,'').replace(/^doi:/i,'')}`:(record.url||'');
  const id=record.pmid?`PMID ${record.pmid}`:(record.doi?`DOI ${record.doi}`:'');const classification=record.search_classification||{};const klass=inferredClass(record);const confidence=classification.confidence||'low';const taxonomy=classification.taxonomy_primary||record.taxonomy_primary||'';const reasons=whyMatched(record);const ranking=rankingSignals(record);const signals=(classification.signals||[]).map(item=>`${item.field}: ${item.value}`);const originalRank=record.reference_rank?`rank final #${record.reference_rank}`:'';const providers=providerValues(record);const providerText=providers.map(providerLabel).join(' + ')||'Fonte não informada';const multiSource=providers.length>1?`<span class="multi-source-pill">${providers.length} fontes</span>`:'';
  return `<article class="result-card" data-result-index="${entry.index}"><div class="result-top"><div class="rank" title="Posição na visualização atual">${viewPosition}</div><div style="flex:1"><h3>${esc(record.title||'(sem título)')}</h3><div class="meta"><span>${esc(record.journal||'—')}</span><span>${esc(record.year||'—')}</span><span>${esc(providerText)}</span>${multiSource}<span>${esc(id)}</span>${originalRank?`<span>${esc(originalRank)}</span>`:''}</div><div class="classification-row"><span class="class-pill">${esc(documentClassLabel(klass))}</span><span class="confidence-pill">Confiança da classificação: ${esc(CONFIDENCE_LABELS[confidence]||confidence)}</span>${taxonomy?`<span class="taxonomy-pill">${esc(taxonomyLabel(taxonomy))}</span>`:''}</div></div><div class="score"><strong>${number(record.reference_score,0).toFixed(1)}</strong><span>ranking final</span></div></div>${reasons.length?`<div class="why-match"><strong>Por que foi recuperado</strong><span>${reasons.map(esc).join(' · ')}</span></div>`:''}${ranking.length?`<div class="why-match"><strong>Sinais do ranking final</strong><span>${ranking.map(esc).join(' · ')}</span></div>`:''}${provenanceDetails(record)}${signals.length?`<div class="result-signals"><strong>Como foi classificado:</strong> ${signals.map(esc).join(' · ')}</div>`:''}${record.abstract?`<div class="abstract">${esc(record.abstract).slice(0,900)}${String(record.abstract).length>900?'…':''}</div>`:''}${href?`<div class="links"><a href="${esc(href)}" target="_blank" rel="noopener noreferrer">Abrir fonte ↗</a></div>`:''}</article>`;
}

function renderFilteredResults(){
  if(!latestSearch)return;const root=$('#results');if(!root)return;
  const entries=filteredEntries();const visible=entries.slice(0,visibleResults);
  const count=$('#facetResultCount');if(count)count.textContent=entries.length.toLocaleString('pt-BR');
  root.innerHTML=visible.map((entry,index)=>resultCard(entry,index+1)).join('')||'<div class="card facet-empty"><strong>Nenhum resultado corresponde a estes filtros.</strong><p>Limpe um filtro ou ajuste a busca dentro dos resultados.</p></div>';
  if(visible.length<entries.length){const more=document.createElement('div');more.className='card facet-load-more';more.innerHTML=`<div class="section-head"><div><strong>${visible.length.toLocaleString('pt-BR')} de ${entries.length.toLocaleString('pt-BR')}</strong><p>Filtros e ordenação atuam sobre o conjunto retornado sem refazer a busca nas fontes.</p></div><button class="ghost" id="facetLoadMore">Carregar mais ${Math.min(RESULT_BATCH,entries.length-visible.length)}</button></div>`;root.appendChild(more);$('#facetLoadMore').addEventListener('click',()=>{visibleResults+=RESULT_BATCH;renderFilteredResults()})}
  window.NutEVSearchUX?.compactCards?.();
}

function enhance(){
  const summary=$('#summary');
  const existingWorkspace=$('#resultFacetWorkspace');
  if(!summary)return;
  if(summary.classList.contains('hidden')){
    existingWorkspace?.classList.add('hidden');
    return;
  }
  if(!latestSearch)return;
  const workspace=ensureWorkspace();if(!workspace)return;
  if(workspace.dataset.searchKey!==currentSearchKey)populateWorkspace();
  workspace.classList.remove('hidden');
  renderFilteredResults();
}

const summary=$('#summary');
if(summary)new MutationObserver(()=>setTimeout(enhance,0)).observe(summary,{childList:true,attributes:true,attributeFilter:['class']});
window.addEventListener('pageshow',()=>{const cached=window.NutEVSearchEvents?.getLastResult?.();if(cached)captureResult(cached);else setTimeout(enhance,0)});

window.NutEVSearchFacets={filteredEntries,renderFilteredResults,providerValues};