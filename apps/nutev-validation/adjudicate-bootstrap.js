const root = document.querySelector('#adjudicationApp')

function esc(value) {
  return String(value ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;')
}

function shell(content) {
  return `<div class="unified-shell">
    <aside class="product-sidebar">
      <div class="product-brand"><div class="product-brand-mark">N</div><div><strong>NutEV</strong><span>Evidence Engine</span></div></div>
      <nav class="product-nav">
        <a href="/">⌕ <span>Buscar evidências</span></a>
        <a href="/?view=history">◷ <span>Minhas buscas</span></a>
        <a class="active" href="/validation/">✓ <span>Validação científica</span></a>
      </nav>
      <div class="product-sidebar-note">A adjudicação só é liberada depois que a rodada científica estiver preparada e os julgamentos iniciais tiverem sido enviados e travados.</div>
    </aside>
    <section class="workspace"><main class="adjudication-main">${content}</main></section>
  </div>`
}

function renderUnavailable(readiness, message = '') {
  const status = readiness?.status || 'unavailable'
  const detail = message || readiness?.message || 'A rodada científica ainda não está pronta para adjudicação.'
  root.innerHTML = shell(`<section class="card"><span class="eyebrow">adjudicação</span><h1>Etapa ainda não preparada</h1><div class="notice">${esc(detail)}</div><p class="muted">Estado: <strong>${esc(status)}</strong>. Nenhuma decisão, conflito ou ausência de evidência é inferida a partir deste estado operacional.</p><a class="btn" href="/validation/">Voltar ao painel de validação</a></section>`)
}

async function readiness() {
  const response = await fetch('/api/validation/readiness', { cache: 'no-store' })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(payload.message || payload.error || 'readiness unavailable')
  return payload
}

async function init() {
  try {
    const state = await readiness()
    if (!state.ready) {
      renderUnavailable(state)
      return
    }
    await import('./adjudicate.js')
  } catch (error) {
    renderUnavailable(null, error.message)
  }
}

init()
