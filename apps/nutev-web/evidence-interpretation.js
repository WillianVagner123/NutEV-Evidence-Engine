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
  let renderQueued=false;

  function rail(){
    const stages=[
      ['map','Structure','Evidence Map','/evidence-map.html'],
      ['intelligence','Inspect','Scientific Intelligence','/intelligence.html'],
      ['review','Human review','Review Control','/review.html']
    ];
    const stageHtml=([key,label,name,href],index)=>{
      const inner=`<span class="ei-step">${index+1}</span><span><strong>${esc(label)}</strong><small>${esc(name)}</small></span>`;
      return key===page
        ?`<span class="ei-stage active" aria-current="page">${inner}</span>`
        :`<a class="ei-stage" href="${href}">${inner}</a>`;
    };
    return `<div class="ei-rail" aria-label="Evidence interpretation navigation">${stages.map(stageHtml).join('<span class="ei-arrow" aria-hidden="true">→</span>')}</div>`;
  }

  function mount(){
    if(document.querySelector('#evidenceInterpretationVisuals'))return;
    const anchor=page==='map'?document.querySelector('.evidence-map-hero'):page==='intelligence'?document.querySelector('.project-hero'):document.querySelector('#reviewContextCard');
    if(!anchor)return;
    const section=document.createElement('section');
    section.id='evidenceInterpretationVisuals';
    section.className='card ei-panel';
    section.innerHTML=`<div class="ei-head"><div><span class="ei-eyebrow">INTERPRETATION WORKFLOW · NAVIGATION ONLY</span><h2>Structure → Inspect → Human review</h2><p>O trilho organiza a leitura entre superfícies. Ele não promove elegibilidade, inclusão, certeza, consenso, EvidenceClaim, recomendação ou PRISMA.</p></div></div>${rail()}<div id="evidenceInterpretationBody" class="ei-body" aria-live="polite"></div>`;
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
    if(!rows.length){body.innerHTML='<div class="ei-empty">Aguardando a matriz estrutural verificada.</div>';return}
    const max=Math.max(1,...rows.map(item=>item.documents));
    body.innerHTML=`<div class="ei-section-head"><div><strong>Domain concentration navigator</strong><span>Contagens estruturais do mapa atual. Clique para aplicar/remover o filtro de domínio existente.</span></div><span class="ei-boundary-chip">volume ≠ strength</span></div><div class="ei-bars">${rows.map(item=>{
      const active=item.domain===selected;
      const width=clamp(100*item.documents/max);
      return `<button type="button" class="ei-bar-button${active?' active':''}" data-ei-map-domain="${esc(item.domain)}" aria-pressed="${active?'true':'false'}"><span class="ei-bar-label"><strong>${esc(item.label)}</strong><small>${item.documents} mapped placements</small></span><span class="ei-track" aria-hidden="true"><i style="--ei-width:${width}%"></i></span></button>`;
    }).join('')}</div><p class="ei-note">Uma mesma referência pode contribuir para mais de um domínio. Concentração e célula vazia não representam qualidade, certeza, ausência de literatura ou evidence gap.</p>`;
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
    if(!rows.length){body.innerHTML='<div class="ei-empty">Aguardando a síntese estrutural rank-blind.</div>';return}
    const max=Math.max(1,...rows.map(item=>item.documents));
    body.innerHTML=`<div class="ei-section-head"><div><strong>Domain inspection panorama</strong><span>Documentos mapeados e materialização de result bundles para inspeção.</span></div><span class="ei-boundary-chip">finding-ready ≠ accepted claim</span></div><div class="ei-domain-grid">${rows.map(item=>{
      const documentWidth=clamp(100*item.documents/max);
      const readyWidth=item.documents?clamp(100*item.findingReady/item.documents):0;
      return `<button type="button" class="ei-domain-button${item.active?' active':''}" data-ei-intelligence-domain="${esc(item.domain)}" aria-pressed="${item.active?'true':'false'}"><span class="ei-domain-top"><strong>${esc(item.label)}</strong><b>${item.documents}</b></span><span class="ei-dual-track"><i class="ei-docs" style="--ei-width:${documentWidth}%"></i><i class="ei-ready" style="--ei-width:${readyWidth}%"></i></span><small>${item.findingReady}/${item.documents} com result bundle materializado</small></button>`;
    }).join('')}</div><div class="ei-legend"><span><i class="ei-legend-docs"></i> corpus mapeado</span><span><i class="ei-legend-ready"></i> finding-ready dentro do domínio</span></div><p class="ei-note">Finding-ready descreve disponibilidade técnica de result bundle. Não significa força, convergência, certeza, elegibilidade nem EvidenceClaim aceito.</p>`;
    body.querySelectorAll('[data-ei-intelligence-domain]').forEach(button=>button.addEventListener('click',()=>{
      const target=[...document.querySelectorAll('[data-select-domain]')].find(node=>node.dataset.selectDomain===button.dataset.eiIntelligenceDomain);
      target?.click();
    }));
  }

  function reviewModel(){
    return [...document.querySelectorAll('.review-round-card')].map((card,index)=>{
      const title=card.querySelector('h3')?.textContent?.trim()||`Round ${index+1}`;
      const progress=card.querySelector('.review-round-head > strong')?.textContent||'';
      const match=progress.match(/(\d+)\s*\/\s*(\d+)/);
      const submitted=match?Number(match[1]):0;
      const reviewers=match?Number(match[2]):0;
      const status=card.querySelector('.mini-pill')?.textContent?.trim()||'status';
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
    return `<div class="ei-assignment"><span><strong>Minha avaliação aberta</strong><small>${completed}/${total} itens com decisão salva</small></span><span class="ei-track" aria-hidden="true"><i style="--ei-width:${width}%"></i></span></div>`;
  }

  function renderReview(){
    const body=document.querySelector('#evidenceInterpretationBody');
    if(!body)return;
    const rows=reviewModel();
    if(!rows.length){body.innerHTML='<div class="ei-empty">Nenhum round explícito desta ResearchApplication para visualizar. O painel não importa rounds legados nem infere bindings.</div>';return}
    body.innerHTML=`<div class="ei-section-head"><div><strong>Human submission progress</strong><span>Progresso de envio por round explicitamente vinculado à aplicação atual.</span></div><span class="ei-boundary-chip">submission ≠ scientific outcome</span></div><div class="ei-review-list">${rows.map(item=>{
      const width=item.reviewers?clamp(100*item.submitted/item.reviewers):0;
      return `<button type="button" class="ei-review-round" data-ei-review-index="${item.index}"><span class="ei-review-top"><strong>${esc(item.title)}</strong><span>${esc(item.status)}${item.assigned?' · atribuído a mim':''}</span></span><span class="ei-track" aria-hidden="true"><i style="--ei-width:${width}%"></i></span><small>${item.submitted}/${item.reviewers} revisores enviaram e travaram a própria avaliação</small></button>`;
    }).join('')}</div>${assignmentProgressHtml()}<p class="ei-note">A barra mede somente submissão humana registrada. Ela não calcula inclusão, concordância, adjudicação científica, risco de viés, certeza ou PRISMA.</p>`;
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
