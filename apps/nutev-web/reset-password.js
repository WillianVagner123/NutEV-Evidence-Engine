import {accessT,applyAccessCopy} from './access-i18n.js'

const params=new URLSearchParams(location.search)
const token=String(params.get('token')||'').trim()
if(token)history.replaceState({},'',location.pathname)

const loading=document.querySelector('#resetLoading')
const person=document.querySelector('#resetPerson')
const personName=document.querySelector('#resetName')
const personEmail=document.querySelector('#resetEmail')
const personExpiry=document.querySelector('#resetExpiry')
const form=document.querySelector('#resetPasswordForm')
const password=document.querySelector('#resetPassword')
const confirmation=document.querySelector('#resetConfirmation')
const submit=document.querySelector('#resetSubmit')
const statusNode=document.querySelector('#resetStatus')
let resetInfo=null

function setStatus(message,tone=''){
  statusNode.textContent=message
  statusNode.className=`access-status${tone?` ${tone}`:''}`
}
function locale(){return window.NutEVI18n?.language==='en'?'en-US':'pt-BR'}
function renderReset(){
  if(!resetInfo)return
  personName.textContent=resetInfo.display_name||''
  personEmail.textContent=resetInfo.email||''
  if(resetInfo.expires_at){
    const date=new Date(resetInfo.expires_at)
    personExpiry.textContent=accessT(`Link válido até ${date.toLocaleString(locale())}.`,`Link valid until ${date.toLocaleString(locale())}.`)
  }
}
async function readJson(response){try{return await response.json()}catch{return{}}}

async function validateReset(){
  if(!token){
    loading.hidden=true
    setStatus(accessT('Este link de redefinição está incompleto. Solicite um novo link.','This reset link is incomplete. Request a new link.'),'error')
    return
  }
  try{
    const response=await fetch(`/api/auth/password-reset/status?token=${encodeURIComponent(token)}`,{credentials:'same-origin',cache:'no-store'})
    const body=await readJson(response)
    if(!response.ok)throw new Error('service_unavailable')
    if(!body?.valid){
      loading.hidden=true
      setStatus(accessT('Este link é inválido, já foi utilizado ou expirou.','This link is invalid, already used, or expired.'),'error')
      return
    }
    resetInfo=body
    loading.hidden=true
    person.hidden=false
    form.hidden=false
    renderReset()
    password.focus()
  }catch{
    loading.hidden=true
    setStatus(accessT('Não foi possível validar o link agora. Tente novamente.','Could not validate the link right now. Try again.'),'error')
  }
}

form?.addEventListener('submit',async event=>{
  event.preventDefault()
  if(!form.reportValidity())return
  if(password.value!==confirmation.value){
    setStatus(accessT('As duas senhas precisam ser iguais.','The two passwords must match.'),'error')
    confirmation.focus()
    return
  }
  submit.disabled=true
  password.disabled=true
  confirmation.disabled=true
  setStatus(accessT('Atualizando sua senha…','Updating your password…'))
  try{
    const response=await fetch('/api/auth/password-reset/confirm',{
      method:'POST',credentials:'same-origin',cache:'no-store',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({token,password:password.value})
    })
    const body=await readJson(response)
    if(!response.ok){
      if(body?.error==='invalid_or_expired_password_reset')throw new Error(accessT('Este link expirou ou já foi utilizado.','This link expired or has already been used.'))
      if(body?.error==='invalid_password')throw new Error(accessT('A senha precisa ter pelo menos 12 caracteres.','The password must contain at least 12 characters.'))
      if(response.status===429)throw new Error(accessT('Muitas tentativas. Aguarde e tente novamente.','Too many attempts. Wait and try again.'))
      throw new Error(accessT('Não foi possível redefinir a senha.','Could not reset the password.'))
    }
    password.value=''
    confirmation.value=''
    form.hidden=true
    setStatus(accessT('Senha atualizada. Todas as sessões anteriores foram encerradas. Entre novamente no NutEV.','Password updated. All previous sessions were revoked. Sign in to NutEV again.'),'success')
  }catch(error){
    setStatus(error?.message||accessT('Não foi possível redefinir a senha.','Could not reset the password.'),'error')
    submit.disabled=false
    password.disabled=false
    confirmation.disabled=false
  }
})

window.addEventListener('nutev:language-change',()=>{applyAccessCopy();renderReset()})
applyAccessCopy()
validateReset()
