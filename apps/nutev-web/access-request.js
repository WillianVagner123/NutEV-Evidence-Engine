import {accessT,applyAccessCopy} from './access-i18n.js'

const form=document.querySelector('#accessRequestForm')
const submit=document.querySelector('#accessRequestSubmit')
const statusNode=document.querySelector('#accessRequestStatus')

function setStatus(message,tone=''){
  statusNode.textContent=message
  statusNode.className=`access-status${tone?` ${tone}`:''}`
}

async function readJson(response){
  try{return await response.json()}catch{return{}}
}

form?.addEventListener('submit',async event=>{
  event.preventDefault()
  if(!form.reportValidity())return
  submit.disabled=true
  setStatus(accessT('Enviando solicitação…','Submitting request…'))
  const payload={
    display_name:String(document.querySelector('#accessName')?.value||'').trim(),
    email:String(document.querySelector('#accessEmail')?.value||'').trim(),
    institution:String(document.querySelector('#accessInstitution')?.value||'').trim(),
    intended_use:String(document.querySelector('#accessUse')?.value||'').trim(),
    website:String(document.querySelector('#accessWebsite')?.value||'').trim()
  }
  try{
    const response=await fetch('/api/access-requests',{
      method:'POST',
      credentials:'same-origin',
      cache:'no-store',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(payload)
    })
    const body=await readJson(response)
    if(!response.ok){
      if(response.status===429)throw new Error(accessT('Muitas solicitações desta origem. Tente novamente mais tarde.','Too many requests from this origin. Try again later.'))
      if(response.status===503)throw new Error(accessT('O serviço de solicitação está temporariamente indisponível.','The access-request service is temporarily unavailable.'))
      throw new Error(accessT('Revise os campos e tente novamente.','Review the fields and try again.'))
    }
    if(body?.status!=='received')throw new Error(accessT('Não foi possível confirmar o recebimento.','Could not confirm receipt.'))
    form.reset()
    setStatus(accessT(
      'Solicitação recebida. Se ela for aprovada, um administrador fornecerá um link temporário para você criar sua senha.',
      'Request received. If approved, an administrator will provide a temporary link for you to create your password.'
    ),'success')
  }catch(error){
    setStatus(error?.message||accessT('Não foi possível enviar a solicitação.','Could not submit the request.'),'error')
  }finally{
    submit.disabled=false
    applyAccessCopy()
  }
})
