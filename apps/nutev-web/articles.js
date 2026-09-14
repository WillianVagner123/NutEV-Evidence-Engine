import './i18n.js';
import{canonicalDocumentClass,documentClassLabel,documentSubtypeLabel}from'./document-classes.js';

const state={cursor:null,loading:false,selected:null,debounce:null};
const $=selector=>document.querySelector(selector);
const esc=value=>String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');
const english=()=>window.NutEVI18n?.language==='en';
const t=(pt,en)=>english()?en:pt;
const fmt=value=>new Intl.NumberFormat(english()?'en-US':'pt-BR').format(Number(value||0));
const fmtScore=value=>value===null||value===undefined||value===''?'—':Number(value).toLocaleString(english()?'en-US':'pt-BR',{maximumFractionDigits:2});
const label=(table,key)=>table[key]?.[english()?1:0]||key;

const kindLabels={objective:['Objetivo','Objective'],method:['Método / contexto','Method / context'],main_result:['Resultado principal','Main result'],secondary_result:['Resultado secundário','Secondary result'],conclusion:['Conclusão','Conclusion'],limitation:['Limitação','Limitation'],disclosure:['Financiamento / conflitos','Funding / conflicts']};
const domainLabels={nutrition_assessment:['Avaliação nutricional','Nutrition assessment'],dietary_counseling:['Aconselhamento alimentar','Dietary counseling'],nutrition_prescription:['Prescrição nutricional','Nutrition prescription'],monitoring_follow_up:['Monitoramento / seguimento','Monitoring / follow-up'],food_skills_competencies:['Competências e habilidades alimentares','Food skills and competencies'],food_literacy:['Literacia alimentar / nutricional','Food / nutrition literacy'],social_context:['Contexto social da alimentação','Social context of eating'],food_based_guidance:['Orientação baseada em alimentos','Food-based guidance'],nutrition_care_process:['Processo de Cuidado em Nutrição','Nutrition Care Process'],lifestyle_medicine:['Medicina do Estilo de Vida','Lifestyle Medicine'],implementation_practice:['Implementação na prática','Implementation in practice']};
const providerLabels={pubmed:'PubMed',europepmc:'Europe PMC',openalex:'OpenAlex',crossref:'Crossref',doaj:'DOAJ',semantic_scholar:'Semantic Scholar',lilacs_bvs_native:'LILACS/BVS',scielo_native:'SciELO'};
const fullTextLabels={retrieved:['Texto completo','Full text'],partial:['Texto parcial','Partial text'],unavailable:['Sem texto completo','Full text unavailable'],not_attempted:['Ainda não buscado','Not yet searched'],not_retrieved:['Não recuperado','Not retrieved']};
const relevanceLabels={high:['aderência operacional alta','high operational match'],medium:['aderência operacional média','medium operational match'],low:['aderência operacional baixa','low operational match']};

function tierFromReference(value){const match=String(value||'').match(/^BANK_([ABCD])_PROCESSING_PRIORITY$/);return match?match[1]:''}
function tierLabel(value){const tier=tierFromReference(value);return tier?`${t('Camada','Tier')} ${tier}`:''}
function classPresentation(raw,canonical=''){
  const canonicalValue=canonical||canonicalDocumentClass(raw);
  const primary=documentClassLabel(canonicalValue);
  const subtype=documentSubtypeLabel(raw);
  return{canonical:canonicalValue,primary,subtype:subtype!==primary?subtype:''};
}

function currentParams(cursor=null){
  const params=new URLSearchParams();
  const q=$('#articleQuery').value.trim();
  const tier=$('#tierFilter').value;
  const sort=$('#sortFilter').value||'relevance';
  const provider=$('#providerFilter').value;
  const docClass=$('#classFilter').value;
  const fullText=$('#fullTextFilter').value;
  const qParts=[];
  if(q)qParts.push(q);
  if(tier)qParts.push(`__nutev_tier:${tier}`);
  if(sort)qParts.push(`__nutev_sort:${sort}`);
  if(qParts.length)params.set('q',qParts.join(' '));
  if(provider)params.set('source_provider',provider);
  if(docClass)params.set('document_class',docClass);
  if(fullText)params.set('full_text_status',fullText);
  if(cursor)params.set('cursor',cursor);
  params.set('limit','50');
  return params;
}

function setState(message,type=''){
  const node=$('#workbenchState');
  node.textContent=message;
  node.className=`workbench-state ${type}`.trim();
}

function articleRow(article){
  const full=label(fullTextLabels,article.full_text_status)||t('Texto não informado','Text status unavailable');
  const fullGood=article.full_text_status==='retrieved';
  const ids=[article.doi?`DOI ${article.doi}`:'',article.pmid?`PMID ${article.pmid}`:''].filter(Boolean);
  const tier=tierLabel(article.reference_tier);
  const priority=[tier,article.reference_rank?`${t('posição','position')} #${fmt(article.reference_rank)}`:'',article.reference_score!==null&&article.reference_score!==undefined?`${t('pontuação operacional','operational score')} ${fmtScore(article.reference_score)}`:''].filter(Boolean);
  const relevance=article.machine_relevance_band?label(relevanceLabels,article.machine_relevance_band):'';
  const classification=classPresentation(article.document_class,article.canonical_document_class);
  return `<button class="article-row${state.selected===article.document_id?' active':''}" type="button" data-document-id="${esc(article.document_id)}">
    <div>
      <div class="article-title">${esc(article.title||t('Sem título','Untitled'))}</div>
      <div class="article-meta">
        <span>${esc(article.year||t('ano n/d','year n/a'))}</span>
        <span>${esc(classification.primary)}</span>
        <span>${esc(providerLabels[article.source_provider]||article.source_provider||t('fonte n/d','source n/a'))}</span>
      </div>
      ${ids.length?`<div class="article-identifiers">${ids.map(id=>`<span>${esc(id)}</span>`).join('')}</div>`:''}
    </div>
    <div class="article-row-side">
      ${classification.subtype?`<span class="mini-pill" title="${esc(t('Subtipo documental preservado no dossiê','Document subtype preserved in the dossier'))}">${esc(classification.subtype)}</span>`:''}
      ${priority.map(value=>`<span class="mini-pill">${esc(value)}</span>`).join('')}
      ${relevance?`<span class="mini-pill">${esc(relevance)}</span>`:''}
      <span class="mini-pill ${fullGood?'good':''}">${esc(full)}</span>
      <span class="mini-pill">${t('contexto estruturado','structured context')} ${fmt(article.llm_context_chars)} ${t('caracteres','characters')}</span>
    </div>
  </button>`;
}

async function loadPage({append=false}={}){
  if(state.loading)return;
  state.loading=true;
  $('#loadMore').disabled=true;
  if(!append)setState(t('Consultando índice…','Querying index…'));
  try{
    const cursor=append?state.cursor:null;
    const response=await fetch(`/api/articles?${currentParams(cursor)}`,{cache:'no-store'});
    const data=await response.json();
    if(!response.ok)throw new Error(data.message||data.error||t('Falha ao consultar artigos','Could not query articles'));
    if(data.status==='not_ready'){
      $('#articleHealth').textContent=t('índice ainda não criado','index not yet created');
      $('#articleHealth').className='status-pill';
      $('#articleCount').textContent='0';
      $('#workbenchContent').classList.add('hidden');
      setState(data.message||t('Biblioteca de evidências ainda sem índice.','Evidence library index is not ready yet.'),'bad');
      return;
    }
    if(data.status!=='ready')throw new Error(data.message||t('Biblioteca de evidências indisponível','Evidence library unavailable'));
    const healthParts=[t('banco','bank')];
    if(data.performance?.server_side_priority_sort)healthParts.push(t('prioridade','priority'));
    if(data.performance?.review_profile_index)healthParts.push(t('perfil científico','scientific profile'));
    $('#articleHealth').textContent=healthParts.join(' + ')+' '+t('verificados','verified');
    $('#articleHealth').className='status-pill ok';
    $('#articleCount').textContent=fmt(data.total_filtered);
    state.cursor=data.next_cursor||null;
    const html=(data.articles||[]).map(articleRow).join('');
    if(append)$('#articleList').insertAdjacentHTML('beforeend',html);
    else $('#articleList').innerHTML=html||`<div class="detail-placeholder"><strong>${t('Nenhum artigo neste filtro.','No article matches this filter.')}</strong><p>${t('Altere a busca ou os filtros.','Change the query or filters.')}</p></div>`;
    $('#loadMore').classList.toggle('hidden',!state.cursor);
    $('#workbenchContent').classList.remove('hidden');
    $('#workbenchState').classList.add('hidden');
  }catch(error){
    $('#articleHealth').textContent=t('erro no índice','index error');
    $('#articleHealth').className='status-pill bad';
    $('#workbenchContent').classList.add('hidden');
    setState(error.message,'bad');
  }finally{
    state.loading=false;
    $('#loadMore').disabled=false;
  }
}

function snapshotHtml(snapshot){
  const entries=Object.entries(snapshot||{}).filter(([,values])=>Array.isArray(values)?values.length:Boolean(values));
  if(!entries.length)return `<p class="provenance">${t('Nenhum campo semântico compacto disponível.','No compact semantic field is available.')}</p>`;
  const labels={objective:['Objetivo','Objective'],population:['População','Population'],sample_size:['Amostra','Sample'],intervention:['Intervenção','Intervention'],exposure:['Exposição','Exposure'],comparator:['Comparador','Comparator'],outcome:['Desfechos','Outcomes'],duration:['Duração','Duration'],follow_up:['Seguimento','Follow-up'],limitation:['Limitações','Limitations']};
  return `<div class="snapshot-grid">${entries.map(([key,values])=>`<div class="snapshot-item"><strong>${esc(label(labels,key))}</strong><span>${esc((Array.isArray(values)?values:[values]).join(' · '))}</span></div>`).join('')}</div>`;
}

function resultHtml(result){
  const numbers=[...(result.effect_measures||[]),...(result.confidence_intervals||[]),...(result.p_values||[])];
  const outcomes=(result.outcomes||[]).filter(Boolean);
  return `<article class="result-card ${result.result_kind==='main_result'?'main':''}">
    <div class="result-card-head"><strong>${result.result_kind==='main_result'?t('Resultado principal','Main result'):t('Resultado secundário','Secondary result')}</strong><span class="mini-pill">${t('candidato','candidate')}</span></div>
    ${outcomes.length?`<div class="provenance"><strong>${t('Desfecho','Outcome')}:</strong> ${esc(outcomes.join(' · '))}</div>`:''}
    ${numbers.length?`<div class="result-numbers">${numbers.map(value=>`<span class="result-number">${esc(value)}</span>`).join('')}</div>`:''}
    <blockquote class="source-quote">${esc(result.result_text||'')}</blockquote>
    <div class="provenance"><strong>${t('Texto processado ou extraído pelo sistema.','Text processed or extracted by the system.')}</strong> ${t('Não é citação literal da fonte e não é EvidenceClaim validada.','It is not a verbatim source quote and it is not a validated EvidenceClaim.')}</div>
  </article>`;
}

function excerptHtml(excerpt){
  const reference=excerpt.reference||{};
  const location=[excerpt.section,excerpt.locator].filter(Boolean).join(' · ');
  const ids=[reference.doi?`DOI ${reference.doi}`:'',reference.pmid?`PMID ${reference.pmid}`:''].filter(Boolean).join(' · ');
  return `<article class="quote-card">
    <div class="quote-head"><span class="quote-kind">${esc(label(kindLabels,excerpt.kind))}</span><span>${esc(location)}</span></div>
    <blockquote class="source-quote">${esc(excerpt.verbatim_excerpt||'')}</blockquote>
    <div class="provenance"><strong>${t('Trecho literal da fonte.','Verbatim source excerpt.')}</strong> ${esc(ids)}${ids?' · ':''}SHA ${esc(String(excerpt.excerpt_sha256||'').slice(0,12))}…</div>
  </article>`;
}

function reviewProfileHtml(profile,machine){
  if(!profile)return `<p class="provenance">${t('Perfil documental ainda não materializado para este artigo.','Document profile has not yet been materialized for this article.')}</p>`;
  const domains=profile.operational_domains||[];
  const matches=profile.operational_domain_matches||{};
  const classification=classPresentation(profile.primary_document_class);
  const band=label(relevanceLabels,machine?.band)||machine?.band||t('n/d','n/a');
  const domainRows=domains.map(domain=>{
    const terms=(matches[domain]||[]).slice(0,6);
    return `<div class="snapshot-item"><strong>${esc(label(domainLabels,domain))}</strong><span>${terms.length?esc(terms.join(' · ')):t('sinal detectado','signal detected')}</span></div>`;
  }).join('');
  return `<div class="detail-chips"><span class="mini-pill">${esc(classification.primary)}</span>${classification.subtype?`<span class="mini-pill">${esc(classification.subtype)}</span>`:''}<span class="mini-pill">${esc(band)}</span><span class="mini-pill">${t('pontuação operacional','operational score')} ${esc(fmtScore(machine?.score))}</span></div>
    ${domainRows?`<div class="snapshot-grid">${domainRows}</div>`:`<p class="provenance">${t('Nenhum domínio operacional específico detectado pelas regras atuais.','No specific operational domain was detected by the current rules.')}</p>`}
    <p class="provenance">${t('Perfil determinístico para navegação. Não é decisão de elegibilidade, inclusão ou exclusão, qualidade, risco de viés, certeza ou recomendação.','Deterministic navigation profile. It is not an eligibility, inclusion/exclusion, quality, risk-of-bias, certainty, or recommendation decision.')}</p>`;
}

function detailHtml(data){
  const card=data.card||{};
  const identity=card.identity||{};
  const reference=card.reference||{};
  const priority=data.bank_priority||{};
  const profile=data.review_profile||null;
  const machine=data.machine_relevance||{};
  const results=data.result_bundles||[];
  const supporting=(data.evidence_excerpts||[]).filter(item=>!['main_result','secondary_result'].includes(item.kind));
  const effectiveClass=data.document_subtype||profile?.primary_document_class||card.document_class;
  const classification=classPresentation(effectiveClass,data.canonical_document_class);
  const chips=[identity.year,classification.primary,classification.subtype,providerLabels[identity.source_provider]||identity.source_provider,label(fullTextLabels,card.full_text_status),tierLabel(priority.reference_tier),priority.reference_rank?`${t('posição','position')} #${fmt(priority.reference_rank)}`:'',priority.reference_score!==null&&priority.reference_score!==undefined?`${t('pontuação operacional','operational score')} ${fmtScore(priority.reference_score)}`:''].filter(Boolean);
  return `<div class="detail-head">
    <h2 id="articleDetailTitle" tabindex="-1">${esc(identity.title||t('Sem título','Untitled'))}</h2>
    <div class="detail-ref">${esc(reference.reference_stub||t('Referência incompleta','Incomplete reference'))}</div>
    <div class="detail-chips">${chips.map(value=>`<span class="mini-pill">${esc(value)}</span>`).join('')}</div>
  </div>
  <section class="detail-section"><h3>${t('Perfil documental','Document profile')}</h3>${reviewProfileHtml(profile,machine)}</section>
  <section class="detail-section"><h3>${t('Visão rápida','Quick view')}</h3>${snapshotHtml(card.study_snapshot)}</section>
  <section class="detail-section"><h3>${t('Principais resultados','Main results')}</h3>${results.length?results.map(resultHtml).join(''):`<p class="provenance">${t('Nenhum pacote de resultados materializado para este artigo.','No result bundle has been materialized for this article.')}</p>`}</section>
  <section class="detail-section"><h3>${t('Trechos-chave','Key excerpts')}</h3>${supporting.length?supporting.map(excerptHtml).join(''):`<p class="provenance">${t('Nenhum trecho adicional selecionado.','No additional excerpt selected.')}</p>`}</section>
  <section class="detail-section"><h3>${t('Prioridade operacional','Operational priority')}</h3>
    <div class="provenance">${esc(tierLabel(priority.reference_tier)||t('Camada n/d','Tier n/a'))} · ${t('posição','position')} ${esc(priority.reference_rank?`#${fmt(priority.reference_rank)}`:t('n/d','n/a'))} · ${t('pontuação operacional','operational score')} ${esc(fmtScore(priority.reference_score))}. ${t('Esses valores orientam ordem de leitura e processamento; não representam julgamento científico.','These values guide reading and processing order; they do not represent scientific judgment.')}</div>
  </section>
  <section class="detail-section"><h3>${t('Proveniência e processamento','Provenance and processing')}</h3>
    <div class="provenance">${t('Registro de cache','Cache record')}: ${esc(String(card.cache_key||'').slice(0,16))}… · ${t('contexto estruturado','structured context')}: ${fmt(card.llm_context_chars)} ${t('caracteres','characters')}. ${t('Esta área mostra metadados e estruturas necessárias à inspeção do documento; detalhes de implementação interna não definem a interpretação científica.','This area shows metadata and structures needed for document inspection; internal implementation details do not define scientific interpretation.')}</div>
  </section>`;
}

function focusDetailOnSingleColumn(){
  if(!window.matchMedia('(max-width: 1100px)').matches)return;
  const detail=$('#articleDetail');
  const title=$('#articleDetailTitle');
  detail?.scrollIntoView({behavior:'smooth',block:'start'});
  title?.focus({preventScroll:true});
}

async function openArticle(documentId){
  state.selected=documentId;
  document.querySelectorAll('.article-row').forEach(row=>row.classList.toggle('active',row.dataset.documentId===documentId));
  $('#articleDetail').innerHTML=`<div class="detail-placeholder"><strong>${t('Carregando dossiê…','Loading dossier…')}</strong></div>`;
  try{
    const response=await fetch(`/api/articles/${encodeURIComponent(documentId)}`,{cache:'no-store'});
    const data=await response.json();
    if(!response.ok)throw new Error(data.message||data.error||t('Artigo não encontrado','Article not found'));
    $('#articleDetail').innerHTML=detailHtml(data);
    requestAnimationFrame(focusDetailOnSingleColumn);
  }catch(error){
    $('#articleDetail').innerHTML=`<div class="detail-placeholder"><strong>${t('Não foi possível abrir o artigo.','Could not open the article.')}</strong><p>${esc(error.message)}</p></div>`;
  }
}

function resetAndLoad(){state.cursor=null;state.selected=null;$('#articleDetail').innerHTML=`<div class="detail-placeholder"><div class="placeholder-mark">▤</div><strong>${t('Selecione um artigo','Select an article')}</strong><p>${t('O dossiê abre aqui sem tirar você da lista.','The dossier opens here without taking you away from the list.')}</p></div>`;loadPage();}
function debouncedLoad(){clearTimeout(state.debounce);state.debounce=setTimeout(resetAndLoad,260)}

$('#articleQuery').addEventListener('input',debouncedLoad);
['tierFilter','sortFilter','providerFilter','classFilter','fullTextFilter'].forEach(id=>$('#'+id).addEventListener('change',resetAndLoad));
$('#clearFilters').addEventListener('click',()=>{$('#articleQuery').value='';$('#tierFilter').value='';$('#sortFilter').value='relevance';$('#providerFilter').value='';$('#classFilter').value='';$('#fullTextFilter').value='';resetAndLoad()});
$('#loadMore').addEventListener('click',()=>loadPage({append:true}));
$('#articleList').addEventListener('click',event=>{const row=event.target.closest('.article-row');if(row)openArticle(row.dataset.documentId)});
window.addEventListener('nutev:language-change',resetAndLoad);

loadPage();