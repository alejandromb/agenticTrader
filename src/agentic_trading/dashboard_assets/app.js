"use strict";

const state = { csrf: "", runs: [], selectedRunId: null, workspace: null, selectedReviewId: null };
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
    await loadWorkspace();
    setDateDefaults();
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

async function loadWorkspace() {
  state.workspace = await api("/api/workspace");
  renderWorkspaceData();
}

function renderWorkspaceData() {
  const workspace = state.workspace || { datasets: [], monitors: [], alerts: [], reviews: [] };
  text(byId("dataset-count"), workspace.datasets.length);
  text(byId("monitor-count"), workspace.monitors.length);
  text(byId("open-alert-count"), workspace.alerts.filter((alert) => alert.status === "open").length);
  fillSelect("portfolio-dataset", workspace.datasets, "dataset_id", datasetLabel);
  fillSelect("backtest-dataset", workspace.datasets, "dataset_id", datasetLabel);
  fillSelect("evaluate-dataset", workspace.datasets, "dataset_id", datasetLabel);
  fillSelect("evaluate-monitor", workspace.monitors, "monitor_id", (item) => `${item.name} · ${item.rules.length} rule${item.rules.length === 1 ? "" : "s"}`);
  const eligibleRuns = state.runs.filter((run) => ["watch", "consider_for_portfolio"].includes(run.disposition));
  fillSelect("monitor-run", eligibleRuns, "run_id", runLabel);
  const reviewRuns = state.runs.filter((run) => run.state === "complete" && run.memo_available);
  fillSelect("review-baseline", reviewRuns, "run_id", runLabel);
  fillSelect("review-current", reviewRuns, "run_id", runLabel);
  setFormAvailability("portfolio-form", workspace.datasets.length > 0);
  setFormAvailability("backtest-form", workspace.datasets.length > 0);
  setFormAvailability("monitor-form", eligibleRuns.length > 0);
  setFormAvailability("monitor-evaluate-form", workspace.monitors.length > 0 && workspace.datasets.length > 0);
  setFormAvailability("review-form", reviewRuns.length > 1);
  renderAlerts(workspace.alerts);
  renderReviews(workspace.reviews);
}

function setFormAvailability(formId, available) {
  const button = byId(formId).querySelector('button[type="submit"]');
  button.disabled = !available;
  button.title = available ? "" : "Required eligible artifacts are not available yet.";
}

function fillSelect(id, items, valueKey, labeler) {
  const select = byId(id);
  const previous = select.value;
  select.replaceChildren();
  if (!items.length) {
    const option = node("option", "", "No eligible artifacts");
    option.value = "";
    select.append(option);
    select.disabled = true;
    return;
  }
  select.disabled = false;
  for (const item of items) {
    const option = node("option", "", labeler(item));
    option.value = item[valueKey];
    select.append(option);
  }
  if (items.some((item) => item[valueKey] === previous)) select.value = previous;
}

function datasetLabel(dataset) {
  return `${dataset.source} · ${dataset.start_date} to ${dataset.end_date} · ${dataset.dataset_id.slice(0, 8)}`;
}

function runLabel(run) {
  return `${run.ticker || "Run"} · ${formatDate(run.as_of)} · ${run.run_id.slice(0, 8)}`;
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

function switchWorkspace(name) {
  const research = name === "research";
  document.querySelector(".shell").classList.toggle("tool-mode", !research);
  document.querySelector(".sidebar").classList.toggle("hidden", !research);
  for (const button of document.querySelectorAll("[data-workspace]")) {
    button.classList.toggle("active", button.dataset.workspace === name);
    button.setAttribute("aria-current", button.dataset.workspace === name ? "page" : "false");
  }
  const more = byId("workspace-more");
  more.classList.toggle("tool-active", ["quant", "monitoring"].includes(name));
  more.open = false;
  byId("quant-workspace").classList.toggle("hidden", name !== "quant");
  byId("monitoring-workspace").classList.toggle("hidden", name !== "monitoring");
  byId("reviews-workspace").classList.toggle("hidden", name !== "reviews");
  if (research) {
    byId("empty-state").classList.toggle("hidden", Boolean(state.selectedRunId));
    byId("run-detail").classList.toggle("hidden", !state.selectedRunId);
  } else {
    byId("empty-state").classList.add("hidden");
    byId("run-detail").classList.add("hidden");
  }
  window.scrollTo({ top: 0, behavior: "smooth" });
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
      body: JSON.stringify({ ticker: byId("research-ticker").value, question: byId("research-question").value, form: byId("research-form-type").value }),
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
    await loadWorkspace();
  } catch (error) {
    showToast(error.message, true);
  } finally {
    button.disabled = false;
  }
}

async function submitPriceImport(event) {
  event.preventDefault();
  await withFormButton(event, async () => {
    const file = byId("price-file").files[0];
    if (!file) throw new Error("Choose a price CSV file.");
    const result = await api("/api/prices/import", {
      method: "POST",
      body: JSON.stringify({
        content_base64: await fileBase64(file),
        source: byId("price-source").value,
        adjustment_note: byId("price-adjustment").value,
      }),
    });
    renderQuantResult("Price dataset imported", result);
    event.target.reset();
    byId("price-adjustment").value = "Adjusted-close values supplied by dataset source.";
    await loadWorkspace();
  });
}

async function submitScreen(event) {
  event.preventDefault();
  await withFormButton(event, async () => {
    const result = await api("/api/screens", {
      method: "POST",
      body: JSON.stringify({
        as_of: localDateTimeIso(byId("screen-as-of").value),
        min_revenue_growth: optionalValue("screen-growth"),
        min_operating_margin: optionalValue("screen-margin"),
        min_current_ratio: optionalValue("screen-current"),
        min_free_cash_flow: optionalValue("screen-fcf"),
      }),
    });
    renderQuantResult("Research screen", result);
  });
}

async function submitPortfolio(event) {
  event.preventDefault();
  await withFormButton(event, async () => {
    const file = byId("holdings-file").files[0];
    if (!file) throw new Error("Choose a holdings CSV file.");
    const result = await api("/api/portfolio", {
      method: "POST",
      body: JSON.stringify({
        content_base64: await fileBase64(file),
        dataset_id: byId("portfolio-dataset").value,
        benchmark: byId("portfolio-benchmark").value,
        as_of: byId("portfolio-as-of").value,
      }),
    });
    renderQuantResult("Hypothetical portfolio analysis", result);
  });
}

async function submitBacktest(event) {
  event.preventDefault();
  await withFormButton(event, async () => {
    const result = await api("/api/backtests", {
      method: "POST",
      body: JSON.stringify({
        dataset_id: byId("backtest-dataset").value,
        ticker: byId("backtest-ticker").value,
        benchmark: byId("backtest-benchmark").value,
        short_window: Number(byId("backtest-short").value),
        long_window: Number(byId("backtest-long").value),
        initial_cash: byId("backtest-cash").value,
        transaction_cost_bps: byId("backtest-cost").value,
      }),
    });
    renderQuantResult("Versioned backtest", result);
  });
}

function renderQuantResult(title, result) {
  text(byId("quant-result-title"), title);
  renderJsonResult(byId("quant-result"), result);
  byId("quant-result").scrollIntoView({ behavior: "smooth", block: "center" });
}

async function submitMonitor(event) {
  event.preventDefault();
  await withFormButton(event, async () => {
    let rules;
    try {
      rules = JSON.parse(byId("monitor-rules").value);
    } catch {
      throw new Error("Rules must be valid JSON.");
    }
    const result = await api("/api/monitors", {
      method: "POST",
      body: JSON.stringify({ run_id: byId("monitor-run").value, name: byId("monitor-name").value, rules }),
    });
    renderJsonResult(byId("monitor-result"), result);
    showToast("Monitor created.");
    await loadWorkspace();
  });
}

async function submitMonitorEvaluation(event) {
  event.preventDefault();
  await withFormButton(event, async () => {
    const monitorId = byId("evaluate-monitor").value;
    const result = await api(`/api/monitors/${encodeURIComponent(monitorId)}/evaluate`, {
      method: "POST",
      body: JSON.stringify({ dataset_id: byId("evaluate-dataset").value, as_of: byId("evaluate-as-of").value }),
    });
    renderJsonResult(byId("monitor-result"), result);
    showToast("Monitor evaluated.");
    await loadWorkspace();
  });
}

function renderAlerts(alerts) {
  const list = byId("alert-list");
  list.replaceChildren();
  if (!alerts.length) {
    list.append(node("p", "empty-list", "No monitoring alerts have been recorded."));
    return;
  }
  for (const alert of alerts) {
    const card = node("article", `alert-card ${alert.status}`);
    const copy = node("div");
    copy.append(node("h4", "", `${alert.evidence.ticker || "Rule"} · ${alert.rule_id}`));
    copy.append(node("p", "", `${alert.evidence.type} observed ${alert.evidence.observed} against ${alert.evidence.threshold} · ${alert.status}`));
    card.append(copy);
    if (alert.status === "open") {
      const actions = node("div", "alert-actions");
      const label = node("label", "", "Acknowledgement note");
      const input = node("input");
      input.placeholder = "What did you review?";
      label.append(input);
      const button = node("button", "secondary-button", "Acknowledge");
      button.type = "button";
      button.addEventListener("click", () => acknowledgeAlert(alert.alert_id, input.value, button));
      actions.append(label, button);
      card.append(actions);
    }
    list.append(card);
  }
}

async function acknowledgeAlert(alertId, note, button) {
  button.disabled = true;
  try {
    await api(`/api/alerts/${encodeURIComponent(alertId)}/acknowledge`, { method: "POST", body: JSON.stringify({ note }) });
    showToast("Alert acknowledged.");
    await loadWorkspace();
  } catch (error) {
    showToast(error.message, true);
  } finally {
    button.disabled = false;
  }
}

async function submitReview(event) {
  event.preventDefault();
  await withFormButton(event, async () => {
    const result = await api("/api/reviews", {
      method: "POST",
      body: JSON.stringify({ baseline_run_id: byId("review-baseline").value, current_run_id: byId("review-current").value }),
    });
    await loadWorkspace();
    await openReview(result.review_id);
    showToast("Research refresh review created.");
  });
}

function renderReviews(reviews) {
  const list = byId("review-list");
  list.replaceChildren();
  if (!reviews.length) {
    list.append(node("p", "empty-list", "No research-refresh reviews yet."));
    return;
  }
  for (const review of reviews) {
    const button = node("button", "review-button");
    button.type = "button";
    button.append(node("strong", "", `${review.ticker} research refresh`));
    button.append(node("span", "", `${review.baseline_run_id.slice(0, 8)} → ${review.current_run_id.slice(0, 8)} · ${review.human_outcome?.outcome || "awaiting outcome"}`));
    button.addEventListener("click", () => openReview(review.review_id));
    list.append(button);
  }
}

async function openReview(reviewId) {
  const review = await api(`/api/reviews/${encodeURIComponent(reviewId)}`);
  state.selectedReviewId = reviewId;
  byId("review-detail").classList.remove("hidden");
  text(byId("review-detail-title"), `${review.ticker} · ${review.baseline_run_id.slice(0, 8)} → ${review.current_run_id.slice(0, 8)}`);
  text(byId("review-outcome-badge"), review.human_outcome?.outcome || "Awaiting human outcome");
  const content = review.content;
  const statuses = content.claim_deltas.reduce((counts, item) => ({ ...counts, [item.status]: (counts[item.status] || 0) + 1 }), {});
  const summary = byId("review-summary");
  summary.replaceChildren();
  addReviewSummary(summary, "Claim inventory", Object.entries(statuses).map(([key, value]) => `${value} ${key}`).join(" · "));
  addReviewSummary(summary, "Metric comparisons", `${content.metric_deltas.length} period-labeled deltas`);
  addReviewSummary(summary, "Limitations", `${content.limitations.added.length} added · ${content.limitations.resolved.length} resolved`);
  addReviewSummary(summary, "Monitoring evidence", `${content.linked_alerts.length} linked alerts inside the review window`);
  byId("review-outcome-form").classList.toggle("hidden", Boolean(review.human_outcome));
}

function addReviewSummary(container, title, value) {
  const card = node("div", "review-summary-card");
  card.append(node("strong", "", title), node("p", "", value));
  container.append(card);
}

async function submitReviewOutcome(event) {
  event.preventDefault();
  await withFormButton(event, async () => {
    await api(`/api/reviews/${encodeURIComponent(state.selectedReviewId)}/outcome`, {
      method: "POST",
      body: JSON.stringify({ outcome: byId("review-outcome").value, rationale: byId("review-rationale").value }),
    });
    await loadWorkspace();
    await openReview(state.selectedReviewId);
    showToast("Human review outcome recorded.");
  });
}

function renderJsonResult(container, value) {
  container.replaceChildren();
  const pre = node("pre", "json-result", JSON.stringify(value, null, 2));
  container.append(pre);
}

async function withFormButton(event, action) {
  const button = event.submitter;
  button.disabled = true;
  try {
    await action();
  } catch (error) {
    showToast(error.message, true);
  } finally {
    button.disabled = false;
  }
}

function fileBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("The selected file could not be read."));
    reader.onload = () => resolve(String(reader.result).split(",", 2)[1]);
    reader.readAsDataURL(file);
  });
}

function optionalValue(id) {
  const value = byId(id).value.trim();
  return value === "" ? null : value;
}

function localDateTimeIso(value) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) throw new Error("Choose a valid as-of timestamp.");
  return parsed.toISOString();
}

function setDateDefaults() {
  const now = new Date();
  const date = now.toISOString().slice(0, 10);
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
  byId("screen-as-of").value = local;
  byId("portfolio-as-of").value = date;
  byId("evaluate-as-of").value = date;
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
for (const button of document.querySelectorAll("[data-workspace]")) button.addEventListener("click", () => switchWorkspace(button.dataset.workspace));
for (const disclosure of document.querySelectorAll(".disclosure-grid .tool-disclosure")) {
  disclosure.addEventListener("toggle", () => {
    if (!disclosure.open) return;
    for (const sibling of disclosure.parentElement.querySelectorAll(".tool-disclosure[open]")) {
      if (sibling !== disclosure) sibling.open = false;
    }
  });
}
byId("price-import-form").addEventListener("submit", submitPriceImport);
byId("screen-form").addEventListener("submit", submitScreen);
byId("portfolio-form").addEventListener("submit", submitPortfolio);
byId("backtest-form").addEventListener("submit", submitBacktest);
byId("monitor-form").addEventListener("submit", submitMonitor);
byId("monitor-evaluate-form").addEventListener("submit", submitMonitorEvaluation);
byId("review-form").addEventListener("submit", submitReview);
byId("review-outcome-form").addEventListener("submit", submitReviewOutcome);
byId("refresh-workspace").addEventListener("click", loadWorkspace);
bootstrap();
