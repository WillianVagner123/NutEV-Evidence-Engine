const $=selector=>document.querySelector(selector);
const esc=value=>String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');
const fmt=value=>new Intl.NumberFormat('pt-BR').format(Number(value||0));
const classLabels={food_based_dietary_guideline:'FBDG',clinical_practice_guideline:'Diretriz clínica',consensus_statement:'Consenso',position_statement:'Posicionamento',framework_model:'Estrutura / modelo',competency_curriculum:'Competências / currículo',implementation_evaluation:'Implementação',primary_randomized:'Randomizado',primary_observational:'Observacional',primary_qualitative:'Qualitativo',evidence_synthesis:'Síntese de evidências',review:'Revisão',guidance:'Orientação',unclassified:'Não classificado'};
const domainLabels={nutrition_assessment:'Avaliação nutricional',dietary_counseling:'Aconselhamento alimentar',nutrition_prescription:'Prescrição nutricional',monitoring_follow_up:'Monitoramento / seguimento',food_skills_competencies:'Competências alimentares',food_literacy:'Literacia alimentar / nutricional',social_context:'Contexto social',food_based_guidance:'Orientação baseada em alimentos',nutrition_care_process:'Processo de Cuidado em Nutrição',lifestyle_medicine:'Medicina do Estilo de Vida',implementation_practice:'Implementação'};
const stopWords=new Set(['a','as','o','os','de','da','das','do','dos','e','em','para','por','com','que','quais','qual','como','sobre','the','of','and','for','in','to','which','what','with','from','related','documentos','documento','artigos','artigo']);
let articles=[];
let results=[];
const selected=new Set();

const normalize=value=>String(value??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
const tokens=value=>[...new Set(normalize(value).split(/[^a-z0-9]+/).filter(token=>token.length>2&&!stopWords.has(token)))];
const flatten=value=>Array.isArray(value)?value.flatMap(flatten):value&&typeof value==='object'?Object.values(value).flatMap(flatten):[String(value??'')];
const effectiveClass=row=>row.review_profile?.primary_document_class||row.document_class||'unclassified';
const domains=row=>row.review_profile?.operational_domains||[];
const matchedTerms=row=>[
  ...flatten(row.review_profile?.document_class_matches||{}),
  ...flatten(row.review_profile?.operational_domain_matches||{})
].filter(Boolean);
const language=()=>window.NutEVI18n?.language==='en'?'en':'pt-BR';
const ui=(pt,en)=>language()==='en'?en:pt;

function searchable(row){return normalize([
  row.title,row.reference_stub,effectiveClass(row),classLabels[effectiveClass(row)],
  ...(row.routes||[]),...domains(row),...domains(row).map(value=>domainLabels[value]||value),...matchedTerms(row)
].join(' '))}

function scoreRow(row,questionTokens,questionPhrase){
  const title=normalize(row.title);const body=searchable(row);let score=0;const signals=[];
  if(questionPhrase&&questionPhrase.length>5&&title.includes(questionPhrase)){score+=30;signals.push(ui('frase no título','phrase in title'))}
  let titleHits=0,contextHits=0;
  for(const token of questionTokens){if(title.includes(token)){score+=6;titleHits+=1}else if(body.includes(token)){score+=2;contextHits+=1}}
  if(titleHits)signals.push(ui(`${titleHits} termo${titleHits>1?'s':''} no título`,`${titleHits} term${titleHits>1?'s':''} in title`));
  if(contextHits)signals.push(ui(`${contextHits} termo${contextHits>1?'s':''} no perfil`,`${contextHits} term${contextHits>1?'s':''} in profile`));
  return {score,signals};
}

function filtersMatch(row){
  const route=$('#askRoute').value,domain=$('#askDomain').value,documentClass=$('#askClass').value;
  if(route&&!(row.routes||[]).includes(route))return false;
  if(domain&&!domains(row).includes(domain))return false;
  if(documentClass&&effectiveClass(row)!==documentClass)return false;
  return true;
}

function corpusHref(row){const q=row.doi||row.pmid||row.title||row.document_id;return `/articles.html?q=${encodeURIComponent(q)}`}

function runQuery(){
  const question=$('#askQuestion').value.trim();
  if(!question){results=[];renderResults(ui('Digite uma pergunta para iniciar.','Enter a question to begin.'));return}
  const qTokens=tokens(question),phrase=normalize(question);
  results=articles.filter(filtersMatch).map(row=>({row,...scoreRow(row,qTokens,phrase)})).filter(item=>item.score>0).sort((a,b)=>b.score-a.score||String(b.row.year||'').localeCompare(String(a.row.year||''))).slice(0,50);
  renderResults();
}

function renderResults(emptyMessage=ui('Nenhum documento corresponde à consulta e aos filtros atuais.','No document matches the current query and filters.')){
  $('#askResultMeta').textContent=results.length?ui(`${fmt(results.length)} melhores correspondências no contexto verificado`,`${fmt(results.length)} best matches in the verified context`):ui('0 correspondências','0 matches');
  $('#selectedCount').textContent=ui(`${selected.size} selecionado${selected.size===1?'':'s'}`,`${selected.size} selected`);
  if(!results.length){$('#askResults').innerHTML=`<p class="small-state">${esc(emptyMessage)}</p>`;return}
  $('#askResults').innerHTML=results.map(({row,signals})=>{
    const checked=selected.has(row.document_id)?' checked':'';
    return `<article class="ask-result">
      <label class="ask-select"><input type="checkbox" data-doc="${esc(row.document_id)}"${checked}><span></span></label>
      <div class="ask-result-body">
        <div class="ask-result-top"><strong data-article-title>${esc(row.title||ui('Sem título','Untitled'))}</strong><a href="${corpusHref(row)}">${ui('Abrir dossiê →','Open dossier →')}</a></div>
        <small>${esc([row.year,row.source_provider,classLabels[effectiveClass(row)]||effectiveClass(row)].filter(Boolean).join(' · '))}</small>
        <div class="detail-chips">${(row.routes||[]).map(route=>`<span class="mini-pill">${esc(route)}</span>`).join('')}${domains(row).slice(0,4).map(domain=>`<span class="mini-pill">${esc(domainLabels[domain]||domain)}</span>`).join('')}</div>
        <div class="ask-signals">${signals.map(signal=>`<span>${esc(signal)}</span>`).join('')||`<span>${ui('correspondência de contexto','context match')}</span>`}</div>
      </div>
    </article>`
  }).join('')}

function packetRows(){
  const chosen=selected.size?articles.filter(row=>selected.has(row.document_id)):results.slice(0,8).map(item=>item.row);
  return chosen.slice(0,12)
}

function buildPacket(){
  const question=$('#askQuestion').value.trim();const chosen=packetRows();
  if(!question){$('#contextPacket').value=ui('Digite uma pergunta antes de gerar o pacote.','Enter a question before building the packet.');return}
  const route=$('#askRoute').value||ui('todas as rotas','all routes');
  const domain=$('#askDomain').value||ui('todos os domínios','all domains');
  const documentClass=$('#askClass').value||ui('todos os tipos documentais','all document classes');
  const docs=chosen.map((row,index)=>{
    const ids=[row.doi?`DOI ${row.doi}`:'',row.pmid?`PMID ${row.pmid}`:''].filter(Boolean).join(' · ');
    if(language()==='en')return `${index+1}. ${row.title||'Untitled'} (${row.year||'year unavailable'})\n   document_id: ${row.document_id}\n   ${ids||'DOI/PMID unavailable'}\n   class: ${effectiveClass(row)}\n   routes: ${(row.routes||[]).join(', ')||'unrouted'}\n   domains: ${domains(row).join(', ')||'none mapped'}\n   dossier: ${location.origin}${corpusHref(row)}`;
    return `${index+1}. ${row.title||'Sem título'} (${row.year||'ano indisponível'})\n   document_id: ${row.document_id}\n   ${ids||'DOI/PMID indisponível'}\n   classe: ${effectiveClass(row)}\n   rotas: ${(row.routes||[]).join(', ')||'sem rota'}\n   domínios: ${domains(row).join(', ')||'nenhum mapeado'}\n   dossiê: ${location.origin}${corpusHref(row)}`
  }).join('\n\n');
  if(language()==='en'){
    $('#contextPacket').value=`NUTEV EVIDENCE QUERY PACKET\n\nQUESTION\n${question}\n\nSCOPE\nroute: ${route}\ndomain: ${domain}\ndocument class: ${documentClass}\n\nSUPPORTING DOCUMENTS (${chosen.length})\n${docs||'No supporting documents selected.'}\n\nVERIFIED CONTEXT\n${location.origin}/agent-context/article1/SEARCH_STATE.json\n${location.origin}/agent-context/article1/CONTEXT_MANIFEST.json\n${location.origin}/agent-context/article1/ARTICLE_SUMMARIES.jsonl\n\nANALYSIS RULES\n- Base the analysis on the supporting documents and verified NutEV context above.\n- Keep document metadata and automated profiles separate from human-accepted scientific evidence.\n- Do not treat route membership, retrieval status, document profile or lexical match as eligibility, inclusion, quality, risk of bias, certainty or recommendation.\n- If a claim requires deeper article content, open the Scientific Dossier for that document and state when available context is insufficient.\n- Do not infer PRISMA events or formal-search completion from this packet.\n- Return supporting document IDs alongside substantive claims.\n`;
    return
  }
  $('#contextPacket').value=`PACOTE DE CONSULTA DE EVIDÊNCIAS NUTEV\n\nPERGUNTA\n${question}\n\nRECORTE\nrota: ${route}\ndomínio: ${domain}\ntipo documental: ${documentClass}\n\nDOCUMENTOS DE SUPORTE (${chosen.length})\n${docs||'Nenhum documento de suporte selecionado.'}\n\nCONTEXTO VERIFICADO\n${location.origin}/agent-context/article1/SEARCH_STATE.json\n${location.origin}/agent-context/article1/CONTEXT_MANIFEST.json\n${location.origin}/agent-context/article1/ARTICLE_SUMMARIES.jsonl\n\nREGRAS DE ANÁLISE\n- Baseie a análise nos documentos de suporte e no contexto verificado do NutEV acima.\n- Mantenha metadados e perfis automatizados separados de evidências científicas aceitas por revisão humana.\n- Não trate pertencimento a rota, estado de recuperação, perfil documental ou correspondência lexical como elegibilidade, inclusão, qualidade, risco de viés, certeza ou recomendação.\n- Se uma alegação exigir conteúdo mais profundo, abra o Dossiê Científico daquele documento e declare quando o contexto disponível for insuficiente.\n- Não infira eventos PRISMA nem conclusão da busca formal a partir deste pacote.\n- Informe os IDs dos documentos de suporte junto às alegações substantivas.\n`;
}

function showContextUnavailable(status){
  const missing=Array.isArray(status?.missing_files)?status.missing_files:[];
  const detail=missing.length?ui(` Arquivos ausentes: ${missing.join(', ')}.`,` Missing files: ${missing.join(', ')}.`):'';
  $('#askState').className='warning';
  $('#askState').innerHTML=`<strong>${ui('Contexto científico ainda não materializado neste ambiente.','Scientific context is not materialized in this environment yet.')}</strong><div>${ui('A Consulta de Evidências não interpreta ausência do pacote como zero evidência.','Evidence Query does not interpret a missing packet as zero evidence.')}${esc(detail)}</div>`;
  $('#askContent').classList.add('hidden');
  $('#askHealth').textContent=ui('contexto não materializado','context not materialized');
  $('#askHealth').className='status-pill';
}

async function load(){
  try{
    const statusResponse=await fetch('/api/agent-context/article1/status',{cache:'no-store'});
    if(!statusResponse.ok)throw new Error(`status HTTP ${statusResponse.status}`);
    const status=await statusResponse.json();
    if(!status.available){showContextUnavailable(status);return}
    const baseUrl=String(status.base_url||'/agent-context/article1/');
    const response=await fetch(`${baseUrl}ARTICLE_SUMMARIES.jsonl`,{cache:'no-store'});if(!response.ok)throw new Error(`HTTP ${response.status}`);
    articles=(await response.text()).split(/\r?\n/).filter(Boolean).map(JSON.parse);
    const domainValues=[...new Set(articles.flatMap(domains))].sort((a,b)=>(domainLabels[a]||a).localeCompare(domainLabels[b]||b));
    $('#askDomain').insertAdjacentHTML('beforeend',domainValues.map(value=>`<option value="${esc(value)}">${esc(domainLabels[value]||value)}</option>`).join(''));
    const classes=[...new Set(articles.map(effectiveClass))].sort((a,b)=>(classLabels[a]||a).localeCompare(classLabels[b]||b));
    $('#askClass').insertAdjacentHTML('beforeend',classes.map(value=>`<option value="${esc(value)}">${esc(classLabels[value]||value)}</option>`).join(''));
    $('#askState').className='hidden';$('#askContent').classList.remove('hidden');$('#askHealth').textContent=ui(`${fmt(articles.length)} resumos verificados`,`${fmt(articles.length)} verified summaries`);$('#askHealth').className='status-pill ok';
  }catch(error){$('#askState').className='error';$('#askState').innerHTML=`<strong>${ui('Consulta de Evidências indisponível.','Evidence Query unavailable.')}</strong><div>${esc(error.message)}</div>`;$('#askHealth').textContent=ui('contexto indisponível','context unavailable');$('#askHealth').className='status-pill bad'}
}

$('#runAsk').addEventListener('click',runQuery);
$('#askQuestion').addEventListener('keydown',event=>{if((event.ctrlKey||event.metaKey)&&event.key==='Enter')runQuery()});
$('.ask-suggestions').addEventListener('click',event=>{const button=event.target.closest('[data-question]');if(!button)return;$('#askQuestion').value=button.dataset.question;runQuery()});
for(const id of ['askRoute','askDomain','askClass'])$(id.startsWith('#')?id:`#${id}`).addEventListener('change',()=>{if($('#askQuestion').value.trim())runQuery()});
$('#clearAsk').addEventListener('click',()=>{$('#askQuestion').value='';$('#askRoute').value='';$('#askDomain').value='';$('#askClass').value='';selected.clear();results=[];renderResults(ui('Nenhuma consulta executada.','No query executed.'));$('#contextPacket').value=''});
$('#askResults').addEventListener('change',event=>{const input=event.target.closest('[data-doc]');if(!input)return;if(input.checked)selected.add(input.dataset.doc);else selected.delete(input.dataset.doc);$('#selectedCount').textContent=ui(`${selected.size} selecionado${selected.size===1?'':'s'}`,`${selected.size} selected`)});
$('#buildPacket').addEventListener('click',buildPacket);
$('#copyPacket').addEventListener('click',async()=>{if(!$('#contextPacket').value)buildPacket();if(!$('#contextPacket').value)return;await navigator.clipboard.writeText($('#contextPacket').value);const button=$('#copyPacket');const old=button.textContent;button.textContent=ui('Copiado','Copied');setTimeout(()=>button.textContent=old,1200)});
window.addEventListener('nutev:language-change',()=>{if(results.length)renderResults();});
load();