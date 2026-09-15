import {accessT,applyAccessCopy} from './access-i18n.js'

const params=new URLSearchParams(location.search)
const token=String(params.get('token')||'').trim()
if(token)history.replaceState({},'',location.pathname)

const loading=document.querySelector('#invitationLoading')
const person=document.querySelector('#invitationPerson')
const personName=document.querySelector('#invitationName')
const personEmail=document.querySelector('#invitationEmail')
const personExpiry=document.querySelector('#invitationExpiry')
const form=document.querySelector('#setPasswordForm')
const password=document.querySelector('#newPassword')
const confirmation=document.querySelector('#confirmPassword')
const submit=document.querySelector('#setPasswordSubmit')
const statusNode=document.querySelector('#setPasswordStatus')
let invitation=null

function setStatus(message,tone=''){
  statusNode.textContent=message
  statusNode.className=`access-status${tone?` ${tone}`:''}`
}

function locale(){return window.NutEVI18n?.language==='en'?'en-US':'pt-BR'}

function renderInvitation(){
  if(!invitation)return
  personName.textContent=invitation.display_name||''
  personEmail.textContent=invitation.email||''
  if(invitation.expires_at){
    const date=new Date(invitation.expires_at)
    personExpiry.textContent=accessT(
      `Convite válido até ${date.toLocaleString(locale())}.`,
      `Invitation valid until ${date.toLocaleString(locale())}.`
    )
  }
}

window.addEventListener('nutev:language-change',()=>{
  applyAccessCopy()
  renderInvitation()
})

async function readJson(response){
  try{return await response.json()}catch{return{}}
}

async function validateInvitation(){
  if(!token){
    loading.hidden=true
    setStatus(accessT('Este link de convite está incompleto. Solicite um novo convite ao administrador.','This invitation link is incomplete. Ask the administrator for a new invitation.'),'error')
    return
  }
  try{
    const response=await fetch(`/api/access-invitations/status?token=${encodeURIComponent(token)}`,{
      credentials:'same-origin',cache:'no-store'
    })
    const body=await readJson(response)
    if(!response.ok)throw new Error('service_unavailable')
    if(!body?.valid){
      loading.hidden=true
      setStatus(accessT('Este convite é inválido, já foi utilizado ou expirou.','This invitation is invalid, already used, or expired.'),'error')
      return
    }
    invitation=body
    loading.hidden=true
    person.hidden=false
    form.hidden=false
    renderInvitation()
    password.focus()
  }catch{
    loading.hidden=true
    setStatus(accessT('Não foi possível validar o convite agora. Tente novamente.','Could not validate the invitation right now. Try again.'),'error')
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
  setStatus(accessT('Criando sua conta…','Creating your account…'))
  try{
    const response=await fetch('/api/access-invitations/accept',{
      method:'POST',credentials:'same-origin',cache:'no-store',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({token,password:password.value})
    })
    const body=await readJson(response)
    if(!response.ok){
      if(body?.error==='invalid_or_expired_invitation')throw new Error(accessT('Este convite expirou ou já foi utilizado.','This invitation expired or has already been used.'))
      if(body?.error==='invalid_password')throw new Error(accessT('A senha precisa ter pelo menos 12 caracteres.','The password must contain at least 12 characters.'))
      if(body?.error==='account_already_exists')throw new Error(accessT('Já existe uma conta para este e-mail. Vá para o login.','An account already exists for this email. Go to sign in.'))
      if(response.status===429)throw new Error(accessT('Muitas tentativas. Aguarde e tente novamente.','Too many attempts. Wait and try again.'))
      throw new Error(accessT('Não foi possível criar a conta.','Could not create the account.'))
    }
    password.value=''
    confirmation.value=''
    form.hidden=true
    setStatus(accessT(
      `Conta criada para ${body.email}. Agora entre no NutEV para continuar o onboarding.`,
      `Account created for ${body.email}. Sign in to NutEV to continue onboarding.`
    ),'success')
  }catch(error){
    setStatus(error?.message||accessT('Não foi possível criar a conta.','Could not create the account.'),'error')
    submit.disabled=false
    password.disabled=false
    confirmation.disabled=false
  }
})

validateInvitation()
