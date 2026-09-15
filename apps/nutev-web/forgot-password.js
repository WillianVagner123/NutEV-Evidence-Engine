import {accessT,applyAccessCopy} from './access-i18n.js'

const form=document.querySelector('#forgotPasswordForm')
const email=document.querySelector('#forgotEmail')
const submit=document.querySelector('#forgotSubmit')
const statusNode=document.querySelector('#forgotStatus')

function setStatus(message,tone=''){
  statusNode.textContent=message
  statusNode.className=`access-status${tone?` ${tone}`:''}`
}

async function readJson(response){try{return await response.json()}catch{return{}}}

form?.addEventListener('submit',async event=>{
  event.preventDefault()
  if(!form.reportValidity())return
  submit.disabled=true
  email.disabled=true
  setStatus(accessT('Processando solicitação…','Processing request…'))
  try{
    const response=await fetch('/api/auth/password-reset/request',{
      method:'POST',credentials:'same-origin',cache:'no-store',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({email:email.value})
    })
    await readJson(response)
    if(response.status===429)throw new Error(accessT('Muitas tentativas. Aguarde e tente novamente.','Too many attempts. Wait and try again.'))
    if(!response.ok)throw new Error(accessT('Não foi possível processar a solicitação.','Could not process the request.'))
    form.reset()
    setStatus(accessT(
      'Se existir uma conta ativa para este e-mail, enviaremos as instruções de redefinição.',
      'If an active account exists for this email, reset instructions will be sent.'
    ),'success')
  }catch(error){
    setStatus(error?.message||accessT('Não foi possível processar a solicitação.','Could not process the request.'),'error')
  }finally{
    submit.disabled=false
    email.disabled=false
  }
})

window.addEventListener('nutev:language-change',applyAccessCopy)
applyAccessCopy()
