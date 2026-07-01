"use strict";

const state = { csrf: "", runs: [], selectedRunId: null };
const byId = (id) => document.getElementById(id);

function text(element, value) {
  element.textContent = value == null || value === "" ? "—" : String(value);
}

function node(tag, className, value) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (value != null) text(element, value);
  return element;
}

async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (options.body) headers["Content-Type"] = "application/json";
  if (options.method && options.method !== "GET") headers["X-Agentic-CSRF"] = state.csrf;
  const response = await fetch(path, { ...options, headers });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || `Request failed (${response.status})`);
  return payload;
}

async function bootstrap() {
  try {
    const config = await api("/api/config");
    state.csrf = config.csrf_token;
    setConfigStatus("sec-status", "SEC", config.sec_configured);
    setConfigStatus("ai-status", "OpenAI", config.openai_configured);
    await loadRuns();
  } catch (error) {
    showToast(error.message, true);
  }
}

function setConfigStatus(id, label, ready) {
  const element = byId(id);
  element.classList.add(ready ? "ready" : "missing");
  text(element, `${label} ${ready ? "ready" : "missing"}`);
}

async function loadRuns(selectRunId = null) {
  const payload = await api("/api/runs");
  state.runs = payload.runs;
  renderRuns();
  if (selectRunId) await openRun(selectRunId);
}

function renderRuns() {
  const list = byId("run-list");
  list.replaceChildren();
  if (!state.runs.length) {
    list.append(node("p", "empty-list", "No saved research yet. Start with a ticker above."));
    return;
  }
  for (const run of state.runs) {
    const button = node("button", "run-card");
    button.type = "button";
    button.dataset.runId = run.run_id;
    button.dataset.testid = `run-${run.run_id}`;
    if (run.run_id === state.selectedRunId) button.classList.add("active");
    button.append(node("strong", "", run.ticker || "Research run"));
    const company = node("span", "", run.company_name || run.run_id.slice(0, 16));
    const meta = node("span", "run-meta");
    meta.append(node("span", "", formatDate(run.as_of)));
    meta.append(node("span", "", run.disposition || run.state.replaceAll("_", " ")));
    button.append(company, meta);
    button.addEventListener("click", () => openRun(run.run_id));
    list.append(button);
  }
}

async function openRun(runId) {
  const detail = await api(`/api/runs/${encodeURIComponent(runId)}`);
  state.selectedRunId = runId;
  renderRuns();
  renderDetail(detail);
}

function renderDetail(detail) {
  byId("empty-state").classList.add("hidden");
  byId("run-detail").classList.remove("hidden");
  const subject = detail.memo?.subject || {};
  text(byId("detail-state"), detail.run.state.replaceAll("_", " "));
  text(byId("detail-title"), subject.company_name || subject.ticker || "Research run");
  text(byId("detail-meta"), `${subject.ticker || "Unknown ticker"} · As of ${formatDate(detail.run.as_of)} · ${detail.run.run_id}`);
  text(byId("detail-disposition"), detail.disposition?.status || "Awaiting decision");
  renderMetrics(detail);
  text(byId("memo-thesis"), detail.memo?.executive_view?.thesis || "No canonical memo is available yet.");
  text(byId("memo-counter"), detail.memo?.executive_view?.counter_thesis || "No counter-thesis is available.");
  renderLimitations(detail);
  renderSections(detail.memo?.sections || {});
  byId("decision-panel").classList.toggle("hidden", !detail.can_record_disposition);
}

function renderMetrics(detail) {
  const metrics = byId("metric-grid");
  metrics.replaceChildren();
  const metadata = detail.analysis_metadata || {};
  const values = [
    ["Prompt", metadata.prompt_version],
    ["Input tokens", formatNumber(metadata.input_tokens)],
    ["Output tokens", formatNumber(metadata.output_tokens)],
    ["Model time", metadata.request_duration_ms == null ? null : `${(metadata.request_duration_ms / 1000).toFixed(1)} sec`],
  ];
  for (const [label, value] of values) {
    const card = node("div", "metric");
    card.append(node("span", "", label), node("strong", "", value));
    metrics.append(card);
  }
}

function renderLimitations(detail) {
  const list = byId("limitations");
  list.replaceChildren();
  const limitations = detail.memo?.uncertainties?.map((item) => item.description) || detail.analysis_metadata?.evidence_gaps || [];
  if (!limitations.length) limitations.push("No recorded limitations were available.");
  for (const limitation of limitations) list.append(node("li", "", limitation));
}

function renderSections(sections) {
  const container = byId("memo-sections");
  container.replaceChildren();
  for (const [name, section] of Object.entries(sections)) {
    const article = node("article", "memo-section");
    article.append(node("strong", "", name.replaceAll("_", " ")), node("p", "", section.summary));
    container.append(article);
  }
}

function openResearchDialog() {
  byId("research-message").className = "form-message";
  text(byId("research-message"), "");
  byId("research-dialog").showModal();
  byId("research-ticker").focus();
}

async function submitResearch(event) {
  event.preventDefault();
  const button = byId("submit-research");
  const message = byId("research-message");
  button.disabled = true;
  text(button, "Running research…");
  message.className = "form-message";
  text(message, "Capturing filing evidence and generating the structured memo.");
  try {
    const result = await api("/api/research", {
      method: "POST",
      body: JSON.stringify({ ticker: byId("research-ticker").value, question: byId("research-question").value }),
    });
    byId("research-dialog").close();
    showToast(`${result.ticker} research completed.`);
    await loadRuns(result.run_id);
  } catch (error) {
    message.className = "form-message error";
    text(message, error.message);
  } finally {
    button.disabled = false;
    text(button, "Start evidence run");
  }
}

async function submitDisposition(event) {
  event.preventDefault();
  const button = event.submitter;
  button.disabled = true;
  try {
    await api(`/api/runs/${encodeURIComponent(state.selectedRunId)}/disposition`, {
      method: "POST",
      body: JSON.stringify({ status: byId("disposition-status").value, rationale: byId("disposition-rationale").value }),
    });
    showToast("Human disposition recorded.");
    byId("disposition-rationale").value = "";
    await loadRuns(state.selectedRunId);
  } catch (error) {
    showToast(error.message, true);
  } finally {
    button.disabled = false;
  }
}

function showToast(message, isError = false) {
  const toast = byId("toast");
  text(toast, message);
  toast.classList.remove("hidden");
  toast.style.background = isError ? "var(--danger)" : "var(--accent)";
  window.setTimeout(() => toast.classList.add("hidden"), 4500);
}

function formatDate(value) {
  if (!value) return "Unknown date";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function formatNumber(value) {
  return value == null ? null : new Intl.NumberFormat().format(value);
}

byId("new-research").addEventListener("click", openResearchDialog);
byId("hero-new-research").addEventListener("click", openResearchDialog);
byId("close-research").addEventListener("click", () => byId("research-dialog").close());
byId("cancel-research").addEventListener("click", () => byId("research-dialog").close());
byId("research-form").addEventListener("submit", submitResearch);
byId("disposition-form").addEventListener("submit", submitDisposition);
byId("refresh-runs").addEventListener("click", () => loadRuns(state.selectedRunId));
bootstrap();
