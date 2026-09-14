import './i18n.js';

const path=location.pathname;
const page=path.endsWith('/evidence-map.html')?'map':path.endsWith('/intelligence.html')?'intelligence':path.endsWith('/review.html')?'review':null;

if(page){
  const style=document.createElement('link');
  style.rel='stylesheet';
  style.href='./evidence-interpretation.css';
  document.head.appendChild(style);

  const numberFrom=value=>Number(String(value||'').replace(/[^0-9-]/g,''))||0;
  const esc=value=>String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');
  const clamp=value=>Math.max(0,Math.min(100,Number(value)||0));
  const t=(pt,en)=>window.NutEVI18n?.t(pt,en)??pt;
  let renderQueued=false;

  function rail(){
    const stages=[
      ['map',t('Estruturar','Structure'),t('Mapa de Evidências','Evidence Map'),'/evidence-map.html'],
      ['intelligence',t('Inspecionar','Inspect'),t('Análise de Evidências','Evidence Analysis'),'/intelligence.html'],
      ['review',t('Revisão humana','Human review'),t('Controle de Revisão','Review Control'),'/review.html']
    ];
    const stageHtml=([key,label,name,href],index)=>{
      const inner=`<span class="ei-step">${index+1}</span><span><strong>${esc(label)}</strong><small>${esc(name)}</small></span>`;
      return key===page
        ?`<span class="ei-stage active" aria-current="page">${inner}</span>`
        :`<a class="ei-stage" href="${href}">${inner}</a>`;
    };
    return `<div class="ei-rail" aria-label="${esc(t('Navegação de interpretação de evidências','Evidence interpretation navigation'))}">${stages.map(stageHtml).join('<span class="ei-arrow" aria-hidden="true">→</span>')}</div>`;
  }

  function mount(){
    if(document.querySelector('#evidenceInterpretationVisuals'))return;
    const anchor=page==='map'?document.querySelector('.evidence-map-hero'):page==='intelligence'?document.querySelector('.project-hero'):document.querySelector('#reviewContextCard');
    if(!anchor)return;
    const section=document.createElement('section');
    section.id='evidenceInterpretationVisuals';
    section.className='card ei-panel';
    section.innerHTML=`<div class="ei-head"><div><span class="ei-eyebrow">${t('INTERPRETAÇÃO CIENTÍFICA · SOMENTE NAVEGAÇÃO','SCIENTIFIC INTERPRETATION · NAVIGATION ONLY')}</span><h2>${t('Estruturar → Inspecionar → Revisão humana','Structure → Inspect → Human review')}</h2><p>${t('O trilho organiza a leitura entre superfícies do sistema. Ele não promove elegibilidade, inclusão, certeza, consenso, EvidenceClaim, recomendação ou PRISMA.','The workflow organizes reading across system surfaces. It does not promote eligibility, inclusion, certainty, consensus, EvidenceClaim, recommendation, or PRISMA.')}</p></div></div>${rail()}<div id="evidenceInterpretationBody" class="ei-body" aria-live="polite"></div>`;
    anchor.insertAdjacentElement('afterend',section);
  }

  function mapModel(){
    const rows=[...document.querySelectorAll('#evidenceMatrix tbody tr')].map(row=>{
      const cells=[...row.querySelectorAll('.matrix-cell[data-domain]')];
      const domain=cells[0]?.dataset.domain||'';
      const label=row.querySelector('th[scope="row"]')?.textContent?.trim()||domain;
      const documents=cells.reduce((sum,cell)=>sum+numberFrom(cell.querySelector('strong')?.textContent),0);
      return {domain,label,documents};
    }).filter(item=>item.domain);
    const selected=document.querySelector('#mapDomainFilter')?.value||'';
    return {rows,selected};
  }

  function renderMap(){
    const body=document.querySelector('#evidenceInterpretationBody');
    if(!body)return;
    const {rows,selected}=mapModel();
    if(!rows.length){body.innerHTML=`<div class="ei-empty">${t('Aguardando a matriz estrutural verificada.','Waiting for the verified structural matrix.')}</div>`;return}
    const max=Math.max(1,...rows.map(item=>item.documents));
    body.innerHTML=`<div class="ei-section-head"><div><strong>${t('Navegador de concentração por domínio','Domain concentration navigator')}</strong><span>${t('Contagens estruturais do mapa atual. Clique para aplicar ou remover o filtro de domínio existente.','Structural counts from the current map. Click to apply or remove the existing domain filter.')}</span></div><span class="ei-boundary-chip">${t('volume ≠ força','volume ≠ strength')}</span></div><div class="ei-bars">${rows.map(item=>{
      const active=item.domain===selected;
      const width=clamp(100*item.documents/max);
      return `<button type="button" class="ei-bar-button${active?' active':''}" data-ei-map-domain="${esc(item.domain)}" aria-pressed="${active?'true':'false'}"><span class="ei-bar-label"><strong>${esc(item.label)}</strong><small>${item.documents} ${t('mapeamentos','mapped placements')}</small></span><span class="ei-track" aria-hidden="true"><i style="--ei-width:${width}%"></i></span></button>`;
    }).join('')}</div><p class="ei-note">${t('Uma mesma referência pode contribuir para mais de um domínio. Concentração e célula vazia não representam qualidade, certeza, ausência de literatura ou lacuna de evidência.','The same reference may contribute to more than one domain. Concentration and empty cells do not represent quality, certainty, absence of literature, or an evidence gap.')}</p>`;
    body.querySelectorAll('[data-ei-map-domain]').forEach(button=>button.addEventListener('click',()=>{
      const control=document.querySelector('#mapDomainFilter');
      if(!control)return;
      control.value=control.value===button.dataset.eiMapDomain?'':button.dataset.eiMapDomain;
      control.dispatchEvent(new Event('change',{bubbles:true}));
    }));
  }

  function intelligenceModel(){
    return [...document.querySelectorAll('[data-domain-card]')].map(card=>{
      const domain=card.dataset.domainCard||'';
      const label=card.querySelector('h3')?.textContent?.trim()||domain;
      const documents=numberFrom(card.querySelector('.domain-count')?.textContent);
      const findingReady=numberFrom(card.querySelector('.domain-metric strong')?.textContent);
      return {domain,label,documents,findingReady,active:card.classList.contains('active')};
    }).filter(item=>item.domain);
  }

  function renderIntelligence(){
    const body=document.querySelector('#evidenceInterpretationBody');
    if(!body)return;
    const rows=intelligenceModel();
    if(!rows.length){body.innerHTML=`<div class="ei-empty">${t('Aguardando a síntese estrutural sem uso de ranking científico.','Waiting for the structural synthesis without scientific ranking.')}</div>`;return}
    const max=Math.max(1,...rows.map(item=>item.documents));
    body.innerHTML=`<div class="ei-section-head"><div><strong>${t('Panorama de inspeção por domínio','Domain inspection overview')}</strong><span>${t('Documentos mapeados e disponibilidade de pacotes de resultados para inspeção.','Mapped documents and result-bundle availability for inspection.')}</span></div><span class="ei-boundary-chip">${t('pronto para inspeção ≠ alegação aceita','ready for inspection ≠ accepted claim')}</span></div><div class="ei-domain-grid">${rows.map(item=>{
      const documentWidth=clamp(100*item.documents/max);
      const readyWidth=item.documents?clamp(100*item.findingReady/item.documents):0;
      return `<button type="button" class="ei-domain-button${item.active?' active':''}" data-ei-intelligence-domain="${esc(item.domain)}" aria-pressed="${item.active?'true':'false'}"><span class="ei-domain-top"><strong>${esc(item.label)}</strong><b>${item.documents}</b></span><span class="ei-dual-track"><i class="ei-docs" style="--ei-width:${documentWidth}%"></i><i class="ei-ready" style="--ei-width:${readyWidth}%"></i></span><small>${item.findingReady}/${item.documents} ${t('com pacote de resultados materializado','with a materialized result bundle')}</small></button>`;
    }).join('')}</div><div class="ei-legend"><span><i class="ei-legend-docs"></i> ${t('corpus mapeado','mapped corpus')}</span><span><i class="ei-legend-ready"></i> ${t('pronto para inspeção no domínio','ready for inspection within domain')}</span></div><p class="ei-note">${t('“Pronto para inspeção” descreve disponibilidade técnica de um pacote de resultados. Não significa força, convergência, certeza, elegibilidade nem EvidenceClaim aceita.','“Ready for inspection” describes technical availability of a result bundle. It does not mean strength, convergence, certainty, eligibility, or an accepted EvidenceClaim.')}</p>`;
    body.querySelectorAll('[data-ei-intelligence-domain]').forEach(button=>button.addEventListener('click',()=>{
      const target=[...document.querySelectorAll('[data-select-domain]')].find(node=>node.dataset.selectDomain===button.dataset.eiIntelligenceDomain);
      target?.click();
    }));
  }

  function reviewModel(){
    return [...document.querySelectorAll('.review-round-card')].map((card,index)=>{
      const title=card.querySelector('h3')?.textContent?.trim()||`${t('Rodada','Round')} ${index+1}`;
      const progress=card.querySelector('.review-round-head > strong')?.textContent||'';
      const match=progress.match(/(\d+)\s*\/\s*(\d+)/);
      const submitted=match?Number(match[1]):0;
      const reviewers=match?Number(match[2]):0;
      const status=card.querySelector('.mini-pill')?.textContent?.trim()||t('status','status');
      const assigned=Boolean(card.querySelector('.mini-pill.assigned'));
      return {index,title,submitted,reviewers,status,assigned,card};
    });
  }

  function assignmentProgressHtml(){
    const panel=document.querySelector('#assignmentPanel');
    if(!panel||panel.classList.contains('hidden'))return '';
    const meta=document.querySelector('#assignmentRoundMeta')?.textContent||'';
    const match=meta.match(/(\d+)\s*\/\s*(\d+)/);
    if(!match)return '';
    const completed=Number(match[1]);
    const total=Number(match[2]);
    const width=total?clamp(100*completed/total):0;
    return `<div class="ei-assignment"><span><strong>${t('Minha avaliação aberta','My open assessment')}</strong><small>${completed}/${total} ${t('itens com decisão salva','items with a saved decision')}</small></span><span class="ei-track" aria-hidden="true"><i style="--ei-width:${width}%"></i></span></div>`;
  }

  function renderReview(){
    const body=document.querySelector('#evidenceInterpretationBody');
    if(!body)return;
    const rows=reviewModel();
    if(!rows.length){body.innerHTML=`<div class="ei-empty">${t('Nenhuma rodada explícita desta Aplicação de pesquisa para visualizar. O painel não importa rodadas legadas nem infere vínculos.','No explicit round from this Research Application is available to visualize. The panel does not import legacy rounds or infer bindings.')}</div>`;return}
    body.innerHTML=`<div class="ei-section-head"><div><strong>${t('Progresso de envio humano','Human submission progress')}</strong><span>${t('Progresso de envio por rodada explicitamente vinculada à aplicação atual.','Submission progress by round explicitly bound to the current application.')}</span></div><span class="ei-boundary-chip">${t('envio ≠ resultado científico','submission ≠ scientific outcome')}</span></div><div class="ei-review-list">${rows.map(item=>{
      const width=item.reviewers?clamp(100*item.submitted/item.reviewers):0;
      return `<button type="button" class="ei-review-round" data-ei-review-index="${item.index}"><span class="ei-review-top"><strong>${esc(item.title)}</strong><span>${esc(item.status)}${item.assigned?` · ${t('atribuído a mim','assigned to me')}`:''}</span></span><span class="ei-track" aria-hidden="true"><i style="--ei-width:${width}%"></i></span><small>${item.submitted}/${item.reviewers} ${t('revisores enviaram e travaram a própria avaliação','reviewers submitted and locked their own assessment')}</small></button>`;
    }).join('')}</div>${assignmentProgressHtml()}<p class="ei-note">${t('A barra mede somente submissão humana registrada. Ela não calcula inclusão, concordância, adjudicação científica, risco de viés, certeza ou PRISMA.','The bar measures only recorded human submission. It does not calculate inclusion, agreement, scientific adjudication, risk of bias, certainty, or PRISMA.')}</p>`;
    body.querySelectorAll('[data-ei-review-index]').forEach(button=>button.addEventListener('click',()=>{
      const item=rows[Number(button.dataset.eiReviewIndex)];
      if(!item)return;
      const action=item.card.querySelector('.open-review')||item.card.querySelector('.round-details');
      action?.click();
      item.card.scrollIntoView({behavior:'smooth',block:'center'});
    }));
  }

  function render(){
    mount();
    if(page==='map')renderMap();
    if(page==='intelligence')renderIntelligence();
    if(page==='review')renderReview();
  }

  function scheduleRender(){
    if(renderQueued)return;
    renderQueued=true;
    requestAnimationFrame(()=>{renderQueued=false;render()});
  }

  function watch(selector){
    const node=document.querySelector(selector);
    if(node)new MutationObserver(scheduleRender).observe(node,{childList:true,subtree:true,attributes:true,characterData:true});
  }

  render();
  window.addEventListener('nutev:language-change',()=>{
    document.querySelector('#evidenceInterpretationVisuals')?.remove();
    scheduleRender();
  });
  if(page==='map'){
    watch('#mapContent');
    ['#mapDomainFilter','#mapClassFilter','#mapRouteFilter','#mapViewTabs'].forEach(selector=>document.querySelector(selector)?.addEventListener('change',scheduleRender));
  }
  if(page==='intelligence'){
    watch('#domainSynthesis');
    watch('#findingState');
  }
  if(page==='review'){
    watch('#reviewRounds');
    watch('#assignmentPanel');
    watch('#assignmentRoundMeta');
  }
}
