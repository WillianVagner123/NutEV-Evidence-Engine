const form=document.querySelector('#loginForm')
const email=document.querySelector('#loginEmail')
const password=document.querySelector('#loginPassword')
const submit=document.querySelector('#loginSubmit')
const statusNode=document.querySelector('#loginStatus')

function safeNext(){
  const raw=new URLSearchParams(location.search).get('next')||'/'
  if(!raw.startsWith('/')||raw.startsWith('//')||raw.startsWith('/login.html'))return'/'
  try{
    const url=new URL(raw,location.origin)
    if(url.origin!==location.origin)return'/'
    return`${url.pathname}${url.search}${url.hash}`
  }catch{return'/'}
}

function setStatus(message,tone=''){
  statusNode.textContent=message
  statusNode.className=`login-status${tone?` ${tone}`:''}`
}

async function readJson(response){
  try{return await response.json()}catch{return{}}
}

async function checkRuntime(){
  try{
    const response=await fetch('/api/auth/status',{cache:'no-store',credentials:'same-origin'})
    if(!response.ok)throw new Error('status_unavailable')
    const runtime=await response.json()
    if(runtime.mode!=='pilot'){
      submit.disabled=true
      email.disabled=true
      password.disabled=true
      setStatus('Este ambiente está no modo legado e não oferece login de plataforma.','error')
      return
    }
    const me=await fetch('/api/auth/me',{cache:'no-store',credentials:'same-origin'})
    if(me.ok){location.replace(safeNext());return}
    if(me.status!==401)throw new Error('session_check_unavailable')
  }catch{
    setStatus('Não foi possível verificar o serviço de autenticação. Tente novamente.','error')
  }
}

form?.addEventListener('submit',async event=>{
  event.preventDefault()
  const emailValue=String(email.value||'').trim()
  const passwordValue=String(password.value||'')
  if(!emailValue||!passwordValue){setStatus('Informe e-mail e senha.','error');return}
  submit.disabled=true
  email.disabled=true
  password.disabled=true
  setStatus('Entrando…')
  try{
    const response=await fetch('/api/auth/login',{
      method:'POST',
      credentials:'same-origin',
      cache:'no-store',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({email:emailValue,password:passwordValue})
    })
    const payload=await readJson(response)
    if(!response.ok){
      if(response.status===401)throw new Error('E-mail ou senha inválidos.')
      if(response.status===429)throw new Error('Muitas tentativas de acesso. Tente novamente mais tarde.')
      if(response.status===503)throw new Error('Serviço de autenticação temporariamente indisponível.')
      throw new Error(String(payload?.message||'Não foi possível entrar.'))
    }
    password.value=''
    setStatus(`Sessão iniciada${payload?.user?.display_name?` para ${payload.user.display_name}`:''}.`,'success')
    location.replace(safeNext())
  }catch(error){
    setStatus(error.message||'Não foi possível entrar.','error')
    submit.disabled=false
    email.disabled=false
    password.disabled=false
    password.focus()
  }
})

checkRuntime()
