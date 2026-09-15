import './i18n.js'

function english(){return window.NutEVI18n?.language==='en'}

function accessT(pt,en){return english()?en:pt}

function applyAccessCopy(root=document){
  const useEnglish=english()
  document.querySelectorAll('[data-pt][data-en]').forEach(node=>{
    node.textContent=useEnglish?node.dataset.en:node.dataset.pt
  })
  document.querySelectorAll('[data-pt-placeholder][data-en-placeholder]').forEach(node=>{
    node.setAttribute('placeholder',useEnglish?node.dataset.enPlaceholder:node.dataset.ptPlaceholder)
  })
  document.querySelectorAll('[data-pt-aria][data-en-aria]').forEach(node=>{
    node.setAttribute('aria-label',useEnglish?node.dataset.enAria:node.dataset.ptAria)
  })
  const html=document.documentElement
  const title=useEnglish?html.dataset.titleEn:html.dataset.titlePt
  if(title)document.title=title
}

window.addEventListener('nutev:language-change',()=>applyAccessCopy())
applyAccessCopy()

export {accessT,applyAccessCopy}
