(() => {
  "use strict";

  let reviewToken = "";
  const accessState = document.getElementById("accessState");
  const reviewPanel = document.getElementById("reviewPanel");
  const assignmentList = document.getElementById("assignmentList");
  const reviewerLabel = document.getElementById("reviewerLabel");
  const reviewerSlot = document.getElementById("reviewerSlot");
  const reviewProgress = document.getElementById("reviewProgress");
  const submitButton = document.getElementById("submitReview");
  const submitHint = document.getElementById("submitHint");

  function consumeFragmentToken() {
    const fragment = new URLSearchParams(window.location.hash.slice(1));
    reviewToken = String(fragment.get("token") || "").trim();
    if (window.location.hash) {
      window.history.replaceState(null, "", window.location.pathname);
    }
  }

  function setStatus(message, kind = "") {
    accessState.textContent = message;
    accessState.className = `status-panel${kind ? ` ${kind}` : ""}`;
  }

  async function api(path, options = {}) {
    if (!reviewToken) {
      throw new Error("O link privado não contém uma credencial de revisão válida.");
    }
    const headers = new Headers(options.headers || {});
    headers.set("Authorization", `Bearer ${reviewToken}`);
    if (options.body && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
    const response = await fetch(path, {
      ...options,
      headers,
      credentials: "same-origin",
      cache: "no-store",
    });
    let payload = {};
    try {
      payload = await response.json();
    } catch (_error) {
      payload = {};
    }
    if (!response.ok) {
      const detail = String(payload.message || payload.error || `HTTP ${response.status}`);
      throw new Error(detail);
    }
    return payload;
  }

  function appendMetadata(container, label, value, href = "") {
    const clean = String(value || "").trim();
    if (!clean) return;
    const span = document.createElement("span");
    const strong = document.createElement("strong");
    strong.textContent = `${label}: `;
    span.appendChild(strong);
    if (href) {
      const anchor = document.createElement("a");
      anchor.href = href;
      anchor.target = "_blank";
      anchor.rel = "noopener noreferrer";
      anchor.textContent = clean;
      span.appendChild(anchor);
    } else {
      span.appendChild(document.createTextNode(clean));
    }
    container.appendChild(span);
  }

  function field(labelText, control) {
    const wrapper = document.createElement("div");
    wrapper.className = "field";
    const label = document.createElement("label");
    label.textContent = labelText;
    label.htmlFor = control.id;
    wrapper.append(label, control);
    return wrapper;
  }

  function renderAssignment(item, policy, locked) {
    const data = item.payload || {};
    const card = document.createElement("article");
    card.className = "assignment-card";
    card.dataset.assignmentId = item.assignment_id;

    const head = document.createElement("div");
    head.className = "assignment-head";
    const headingWrap = document.createElement("div");
    const title = document.createElement("h2");
    title.className = "assignment-title";
    title.textContent = String(data.title || "Registro sem título");
    headingWrap.appendChild(title);
    const position = document.createElement("span");
    position.className = "assignment-position";
    position.textContent = String(data.packet_position || "—");
    head.append(headingWrap, position);
    card.appendChild(head);

    const metadata = document.createElement("div");
    metadata.className = "metadata";
    appendMetadata(metadata, "ID", data.record_id);
    appendMetadata(metadata, "Delta", data.delta_id);
    appendMetadata(metadata, "Rota", data.route);
    appendMetadata(metadata, "PMID", data.pmid, data.pmid ? `https://pubmed.ncbi.nlm.nih.gov/${encodeURIComponent(data.pmid)}/` : "");
    appendMetadata(metadata, "DOI", data.doi, data.doi ? `https://doi.org/${encodeURIComponent(data.doi)}` : "");
    appendMetadata(metadata, "Ano", data.year);
    appendMetadata(metadata, "Periódico", data.journal);
    appendMetadata(metadata, "Fonte", data.url, data.url || "");
    card.appendChild(metadata);

    if (data.route_purpose) {
      const purpose = document.createElement("p");
      purpose.className = "route-purpose";
      purpose.textContent = `Propósito da rota: ${data.route_purpose}`;
      card.appendChild(purpose);
    }

    const decisionGrid = document.createElement("div");
    decisionGrid.className = "decision-grid";

    const decision = document.createElement("select");
    decision.id = `decision-${item.assignment_id}`;
    decision.disabled = locked;
    const blank = document.createElement("option");
    blank.value = "";
    blank.textContent = "Selecione";
    decision.appendChild(blank);
    for (const optionValue of policy.decision_options || []) {
      const option = document.createElement("option");
      option.value = optionValue;
      option.textContent = optionValue;
      decision.appendChild(option);
    }

    const reason = document.createElement("textarea");
    reason.id = `reason-${item.assignment_id}`;
    reason.placeholder = "Justificativa obrigatória";
    reason.disabled = locked;

    const notes = document.createElement("textarea");
    notes.id = `notes-${item.assignment_id}`;
    notes.placeholder = "Observação opcional";
    notes.disabled = locked;

    if (item.decision) {
      decision.value = String(item.decision.decision_value || "");
      reason.value = String(item.decision.reason || "");
      notes.value = String(item.decision.notes || "");
    }

    decisionGrid.append(field("Decisão", decision), field("Justificativa", reason));
    const notesField = field("Observação", notes);
    notesField.classList.add("notes-field");
    decisionGrid.appendChild(notesField);
    card.appendChild(decisionGrid);

    const actions = document.createElement("div");
    actions.className = "card-actions";
    const save = document.createElement("button");
    save.className = "save-decision";
    save.type = "button";
    save.textContent = locked ? "Avaliação travada" : "Salvar decisão";
    save.disabled = locked;
    const status = document.createElement("span");
    status.className = `card-status${item.decision ? " saved" : ""}`;
    status.textContent = item.decision ? "Salvo" : "Pendente";

    save.addEventListener("click", async () => {
      const value = decision.value;
      const reasonValue = reason.value.trim();
      if (!value) {
        status.className = "card-status error";
        status.textContent = "Escolha Y, N ou U.";
        return;
      }
      if (!reasonValue) {
        status.className = "card-status error";
        status.textContent = "Informe a justificativa.";
        return;
      }
      save.disabled = true;
      status.className = "card-status";
      status.textContent = "Salvando…";
      try {
        await api("/api/article1/d132/decision", {
          method: "POST",
          body: JSON.stringify({
            assignment_id: item.assignment_id,
            decision_value: value,
            reason: reasonValue,
            notes: notes.value.trim(),
          }),
        });
        status.className = "card-status saved";
        status.textContent = "Salvo";
        await loadReview();
      } catch (error) {
        status.className = "card-status error";
        status.textContent = error.message;
        save.disabled = false;
      }
    });

    actions.append(save, status);
    if (locked) {
      const badge = document.createElement("span");
      badge.className = "locked-badge";
      badge.textContent = "Enviado · travado";
      actions.appendChild(badge);
    }
    card.appendChild(actions);
    return card;
  }

  function renderReview(payload) {
    reviewPanel.hidden = false;
    reviewerLabel.textContent = String(payload.reviewer_label || "Revisor");
    reviewerSlot.textContent = String(payload.reviewer_slot || "—");
    reviewProgress.textContent = `${payload.completed_items || 0}/${payload.total_items || 0}`;
    assignmentList.replaceChildren();
    for (const item of payload.assignments || []) {
      assignmentList.appendChild(renderAssignment(item, payload.policy || {}, Boolean(payload.locked)));
    }
    submitButton.disabled = Boolean(payload.locked) || payload.completed_items !== payload.total_items || !payload.total_items;
    if (payload.locked) {
      submitHint.textContent = "Avaliação enviada e travada. Nenhuma decisão pode ser alterada.";
      submitButton.textContent = "Avaliação enviada";
    } else {
      submitHint.textContent = `Complete todos os registros antes do envio final (${payload.completed_items || 0}/${payload.total_items || 0}).`;
      submitButton.textContent = "Enviar e travar avaliação";
    }
  }

  async function loadReview() {
    try {
      const payload = await api("/api/article1/d132/review");
      setStatus("Acesso privado validado. Exibindo somente os registros atribuídos.", "success");
      renderReview(payload);
    } catch (error) {
      reviewPanel.hidden = true;
      setStatus(error.message, "error");
    }
  }

  submitButton.addEventListener("click", async () => {
    submitButton.disabled = true;
    submitHint.textContent = "Enviando e travando avaliação…";
    try {
      await api("/api/article1/d132/submit", { method: "POST", body: "{}" });
      await loadReview();
    } catch (error) {
      submitHint.textContent = error.message;
      submitButton.disabled = false;
    }
  });

  consumeFragmentToken();
  if (!reviewToken) {
    reviewPanel.hidden = true;
    setStatus("Credencial privada ausente. Reabra o link original de revisão fornecido pelo pesquisador.", "error");
    return;
  }
  loadReview();
})();
