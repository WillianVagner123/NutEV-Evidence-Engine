import './i18n.js'

const $=selector=>document.querySelector(selector);
const esc=value=>String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');
const fmt=value=>new Intl.NumberFormat('pt-BR').format(Number(value||0));
const language=()=>window.NutEVI18n?.language==='en'?'en':'pt-BR';
const ui=(pt,en)=>language()==='en'?en:pt;
const ANALYSIS_INSTRUCTIONS={
  'pt-BR':`Leia primeiro o SEARCH_SUMMARY e o SEARCH_STATE canônicos do Artigo 1 no NutEV. Depois use ARTICLE_SUMMARIES.jsonl como contexto estruturado sem uso de ranking científico. Analise apenas o que os dados suportam. Não trate descoberta, camada do banco, perfil automatizado, pertencimento a rota ou recuperação de texto completo como inclusão científica, qualidade, risco de viés, certeza ou PRISMA. Quando precisar aprofundar um documento específico, use seu document_id no Dossiê Científico e mantenha separados artefatos automatizados e decisões humanas.`,
  en:`Read the canonical Article 1 SEARCH_SUMMARY and SEARCH_STATE in NutEV first. Then use ARTICLE_SUMMARIES.jsonl as structured rank-blind context. Analyze only what the data support. Do not treat discovery, bank tier, automated profile, route membership or full-text retrieval as scientific inclusion, quality, risk of bias, certainty or PRISMA. When deeper inspection of a document is needed, use its document_id in the Scientific Dossier and keep automated artifacts separate from human decisions.`
};

async function getJson(url){const response=await fetch(url,{cache:'no-store'});if(!response.ok)throw new Error(`HTTP ${response.status}`);return response.json()}
function instructions(){return ANALYSIS_INSTRUCTIONS[language()]||ANALYSIS_INSTRUCTIONS['pt-BR']}
function syncInstructions(){$('#agentPrompt').value=instructions()}

function renderUnavailable(status){
  const missing=(status?.missing_files||[]).map(name=>`<code>${esc(name)}</code>`).join(', ');
  $('#aiHealth').textContent=ui('contexto não materializado','context not materialized');$('#aiHealth').className='status-pill';
  $('#contextState').className='dashboard-state';
  $('#contextState').innerHTML=`<strong>${ui('Contexto de Evidências ainda não materializado neste ambiente.','Evidence Context is not materialized in this environment yet.')}</strong><div class="small-state">${missing?ui(`Arquivos pendentes: ${missing}. `,`Pending files: ${missing}. `):''}${ui('Nenhum estado científico foi inferido ou fabricado. Materialize o pacote persistente antes de usar esta área.','No scientific state was inferred or fabricated. Materialize the persistent bundle before using this area.')}</div>`;
  $('#contextContent').classList.add('hidden');
}

function renderCards(manifest,state){
  const runtime=state.runtime||{};
  const cards=[
    [ui('Versão do contexto','Context version'),state.context_version||manifest.context_version||'—'],
    [ui('ID da busca','Search ID'),state.search_id||manifest.search_id||'—'],
    [ui('Resumos de artigos','Article summaries'),runtime.agent_article_summaries||manifest.counts?.article_summaries||0],
    ['B-NORM',runtime.article1_routes?.counts?.['B-NORM']||0],
    ['C-STRUCT',runtime.article1_routes?.counts?.['C-STRUCT']||0],
    [ui('Gate formal','Formal gate'),state.formal_search?.gf10_authorized?ui('AUTORIZADO','AUTHORIZED'):ui('BLOQUEADO','LOCKED')]
  ];
  $('#contextCards').innerHTML=cards.map(([label,value])=>`<article class="card metric-card"><span class="metric-label">${esc(label)}</span><strong class="metric-value ai-value">${typeof value==='number'?fmt(value):esc(value)}</strong></article>`).join('')
}

function renderFiles(manifest){
  const outputs=manifest.outputs||{};
  const fileRows=[
    ['SEARCH_SUMMARY.md','/agent-context/article1/SEARCH_SUMMARY.md',outputs.search_summary?.sha256],
    ['SEARCH_STATE.json','/agent-context/article1/SEARCH_STATE.json',outputs.search_state?.sha256],
    ['ARTICLE_SUMMARIES.jsonl','/agent-context/article1/ARTICLE_SUMMARIES.jsonl',outputs.article_summaries?.sha256],
    ['CONTEXT_MANIFEST.json','/agent-context/article1/CONTEXT_MANIFEST.json',null]
  ];
  $('#contextFiles').innerHTML=fileRows.map(([name,url,sha])=>`<a class="context-file" href="${url}" target="_blank" rel="noopener"><div><strong>${esc(name)}</strong><small>${sha?`SHA-256 ${esc(String(sha).slice(0,18))}…`:ui('manifesto de proveniência','provenance manifest')}</small></div><span>${ui('Abrir','Open')} ↗</span></a>`).join('')
}

function renderFormalState(state){
  $('#formalState').innerHTML=`<div class="readiness-grid"><div class="readiness-item"><span>PRESS</span><strong>${esc(state.formal_search?.press_status||'—')}</strong></div><div class="readiness-item"><span>GF-10</span><strong>${state.formal_search?.gf10_authorized?ui('AUTORIZADO','AUTHORIZED'):ui('BLOQUEADO','LOCKED')}</strong></div><div class="readiness-item"><span>${ui('Congelamento da consulta','Query freeze')}</span><strong>${state.formal_search?.query_freeze_complete?ui('CONCLUÍDO','COMPLETE'):ui('NÃO CONCLUÍDO','NOT COMPLETE')}</strong></div><div class="readiness-item"><span>${ui('Busca formal','Formal search')}</span><strong>${state.formal_search?.formal_provider_search_executed?ui('EXECUTADA','EXECUTED'):ui('NÃO EXECUTADA','NOT EXECUTED')}</strong></div></div>`
}

async function init(){
  try{
    const [health,availability]=await Promise.all([getJson('/api/health'),getJson('/api/agent-context/article1/status')]);
    if(!availability.available){renderUnavailable(availability);return}
    const [manifest,state]=await Promise.all([getJson('/agent-context/article1/CONTEXT_MANIFEST.json'),getJson('/agent-context/article1/SEARCH_STATE.json')]);
    $('#aiHealth').textContent=health.status==='ok'?ui('contexto disponível','context available'):ui('sistema parcial','system partial');$('#aiHealth').className=`status-pill ${health.status==='ok'?'ok':'bad'}`;
    renderCards(manifest,state);renderFiles(manifest);renderFormalState(state);
    $('#contextState').className='hidden';$('#contextContent').classList.remove('hidden');
  }catch(error){$('#aiHealth').textContent=ui('contexto indisponível','context unavailable');$('#aiHealth').className='status-pill bad';$('#contextState').className='error';$('#contextState').innerHTML=`<strong>${ui('Não foi possível verificar o Contexto de Evidências.','Could not verify Evidence Context.')}</strong><div>${esc(error.message)}</div><div class="small-state">${ui('Nenhum estado científico foi inferido. Verifique a disponibilidade e o pacote persistente.','No scientific state was inferred. Verify availability and the persistent bundle.')}</div>`}
}

syncInstructions();
$('#copyPrompt').addEventListener('click',async()=>{await navigator.clipboard.writeText(instructions());$('#copyPrompt').textContent=ui('Copiado','Copied');setTimeout(()=>$('#copyPrompt').textContent=ui('Copiar instruções','Copy instructions'),1400)});
window.addEventListener('nutev:language-change',()=>{syncInstructions();init()});
init();