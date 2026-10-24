// MWP script-model leaderboard. Static page: reads the eval repo's JSON at load.
// Contract: My-Weird-Prompts monorepo PLAN-040 "Data contracts".
// ?base=<url> overrides the data location (e.g. ?base=../../results/ for a local check).
"use strict";

const params = new URLSearchParams(location.search);
const BASE = params.get("base") || "https://raw.githubusercontent.com/My-Weird-Prompts/eval/main/results/";
const SITE = "https://myweirdprompts.com";

const COLS = [
  // [field, label, numeric, title]
  ["model", "model", false, "OpenRouter model id (aired baselines: the show's own writer label)"],
  ["technical_fail", "tech fail", false, "Any refusal by the model or a provider filter"],
  ["v1_score", "V1 score", true, "25 x (priority - 1), gated on parse and length 0.8-1.2x"],
  ["on_length", "on length", true, "Scripts that passed the length gate"],
  ["priority", "priority", true, "Mean of the priority rubric axes (1-5)"],
  ["mid_hold", "mid hold", true, "Long-form coherence: holds the middle (1-5)"],
  ["fun", "fun", true, "1-5"],
  ["candour", "candour", true, "1-5"],
  ["liveness", "liveness", true, "1-5"],
  ["len_ratio", "len ratio", true, "Words / 3,800 target"],
  ["cost_vs_baseline", "cost vs DeepSeek", true, "Episode cost with this writer / DeepSeek V4.1 Flash episode"],
  ["usd_per_script", "$/script", true, "Writer cost per script"],
  ["est_usd_per_episode", "est $/episode", true, "Whole production episode with this writer"],
  ["judge_overall", "judge overall", true, ""],
  ["n", "n", true, "Samples"],
];

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const label = (k) => k.replace(/_/g, " ");

let LB = null;
let sortState = { key: null, dir: -1 };

async function getJSON(name) {
  const r = await fetch(BASE + name, { cache: "no-cache" });
  if (!r.ok) throw new Error(`${name}: HTTP ${r.status}`);
  return r.json();
}

function fmt(v, key) {
  if (v === null || v === undefined) return '<span class="muted">—</span>';
  if (typeof v === "boolean") return v ? '<span class="fail-tag">FAIL</span>' : '<span class="pass-tag">pass</span>';
  if (typeof v === "number") {
    if (key === "cost_vs_baseline") return `${Math.round(v * 100)}%`;
    if (key && key.startsWith("usd") || key === "est_usd_per_episode") return "$" + (v < 0.01 ? v.toPrecision(2) : v.toFixed(3));
    const scoreKey = COLS.some(([k, , num]) => num && k === key) && !["v1_score", "n"].includes(key);
    if (Number.isInteger(v) && !scoreKey) return String(v);
    return Math.abs(v) < 0.1 ? v.toFixed(4) : v.toFixed(2);
  }
  return esc(v);
}

function sortValue(row, key) {
  const v = key.startsWith("extra.") ? (row.extra || {})[key.slice(6)] : row[key];
  if (v === null || v === undefined) return null;
  if (typeof v === "string") {
    const m = v.match(/^(\d+)\/(\d+)$/);
    if (m) return +m[1] / +m[2];
    const n = parseFloat(v);
    return Number.isNaN(n) ? v.toLowerCase() : n;
  }
  if (typeof v === "boolean") return v ? 1 : 0;
  return v;
}

function defaultSortKey(run) {
  for (const k of ["v1_score", "priority", "usd_per_script", "n"]) if (run.rows.some((r) => r[k] != null)) return k;
  return "model";
}

function renderCurrent() {
  const c = LB.current || {};
  // Latest scored row for the current writer.
  let row = null, rowRun = null;
  for (const run of LB.runs) {
    const r = run.rows.find((x) => x.model === c.writer && x.v1_score != null);
    if (r) { row = r; rowRun = run; break; }
  }
  const stats = row ? `<div class="kv">
      <span>latest scored run: <b>${esc(rowRun.run_id)}</b></span>
      <span>V1 score <b>${fmt(row.v1_score)}</b></span>
      <span>on length <b>${fmt(row.on_length)}</b></span>
      <span>mid hold <b>${fmt(row.mid_hold, "mid_hold")}</b></span>
      <span>fun <b>${fmt(row.fun, "fun")}</b></span>
      <span>cost vs DeepSeek <b>${fmt(row.cost_vs_baseline, "cost_vs_baseline")}</b></span>
    </div>` : "";
  $("current").innerHTML = `<div class="current">
      <span class="writer">${esc(c.writer)}</span>
      <span class="meta">writing every pipeline episode since <b>${esc(c.since)}</b>${c.decision ? ` (decision ${esc(c.decision)})` : ""}</span>
      ${c.note ? `<span class="meta small">${esc(c.note)}</span>` : ""}
      ${stats}
    </div>`;
}

function renderPicker() {
  const sel = $("run-picker");
  sel.innerHTML = LB.runs.map((r, i) =>
    `<option value="${i}">${esc(r.date || "")} · ${esc(r.run_id)} (${esc(r.kind)}, ${r.rows.length} models)</option>`).join("");
  // Default: the latest run with V1 scores (a ranked leaderboard); every run stays in the picker.
  let idx = LB.runs.findIndex((r) => r.rows.some((x) => x.v1_score != null));
  if (params.get("run")) {
    const j = LB.runs.findIndex((r) => r.run_id === params.get("run"));
    if (j >= 0) idx = j;
  }
  sel.value = String(Math.max(idx, 0));
  sel.addEventListener("change", () => { sortState = { key: null, dir: -1 }; renderRun(); });
}

function renderRun() {
  const run = LB.runs[+$("run-picker").value];
  const bits = [
    run.kind && `<span class="chip">${esc(run.kind)}</span>`,
    run.benchmark_version && `<span class="chip">benchmark ${esc(run.benchmark_version)}</span>`,
    `<span class="chip">judge: ${esc(run.judge || "none")}</span>`,
    run.spend_usd != null && `<span class="chip">spend ~$${esc(run.spend_usd)}</span>`,
  ].filter(Boolean).join("");
  const extraLinks = [
    run.pdf && `<a href="https://github.com/My-Weird-Prompts/eval/blob/main/${esc(run.pdf)}">reading copy (PDF)</a>`,
    run.hf_dataset && `<a href="https://huggingface.co/datasets/${esc(run.hf_dataset)}">samples on HF</a>`,
    `<a href="https://github.com/My-Weird-Prompts/eval/blob/main/${esc(run.source || "results/README.md")}">write-up</a>`,
  ].filter(Boolean).join(" · ");
  $("run-head").innerHTML = `<p>${bits}</p><p>${esc(run.summary)}</p><p class="small">${extraLinks}</p>`;

  const cols = COLS.filter(([k]) => k === "model" || run.rows.some((r) => r[k] !== null && r[k] !== undefined));
  const extraKeys = [...new Set(run.rows.flatMap((r) => Object.keys(r.extra || {})))];
  const hasNotes = run.rows.some((r) => r.notes);
  if (!sortState.key) sortState = { key: defaultSortKey(run), dir: defaultSortKey(run) === "model" ? 1 : -1 };

  const ranked = cols.some(([k]) => k === "v1_score");
  const rows = [...run.rows].sort((a, b) => {
    // Technical fails always sink to the bottom and are never ranked.
    if (ranked && !!a.technical_fail !== !!b.technical_fail) return a.technical_fail ? 1 : -1;
    const va = sortValue(a, sortState.key), vb = sortValue(b, sortState.key);
    if (va === vb) return 0;
    if (va === null) return 1;
    if (vb === null) return -1;
    return (va < vb ? -1 : 1) * sortState.dir;
  });

  const th = (key, text, num, title) => {
    const aria = sortState.key === key ? ` aria-sort="${sortState.dir > 0 ? "ascending" : "descending"}"` : "";
    return `<th class="${num ? "num" : ""}"${aria} title="${esc(title || "")}"><button data-key="${esc(key)}">${esc(text)}</button></th>`;
  };
  let html = "<thead><tr>" + (ranked ? '<th class="num">#</th>' : "") +
    cols.map(([k, l, num, t]) => th(k, l, num, t)).join("") +
    extraKeys.map((k) => th("extra." + k, label(k), false, "run-specific column")).join("") +
    (hasNotes ? "<th>notes</th>" : "") + "</tr></thead><tbody>";
  let rank = 0;
  for (const r of rows) {
    const cur = r.model === LB.current?.writer;
    html += `<tr class="${r.technical_fail ? "fail" : ""}">`;
    if (ranked) html += `<td class="num">${r.technical_fail ? "—" : ++rank}</td>`;
    for (const [k, , num] of cols) {
      if (k === "model") html += `<td class="model${cur ? " is-current" : ""}" title="${esc(r.exclusion || "")}">${esc(r.model)}${cur ? " ★" : ""}</td>`;
      else html += `<td class="${num ? "num" : ""}">${fmt(r[k], k)}</td>`;
    }
    for (const k of extraKeys) {
      const v = (r.extra || {})[k];
      html += `<td class="${typeof v === "number" ? "num" : ""}">${fmt(v, k)}</td>`;
    }
    if (hasNotes) html += `<td class="notes">${esc(r.notes || "")}</td>`;
    html += "</tr>";
  }
  $("board").innerHTML = html + "</tbody>";
  $("board").querySelectorAll("th button").forEach((b) => b.addEventListener("click", () => {
    const key = b.dataset.key;
    sortState = sortState.key === key ? { key, dir: -sortState.dir } : { key, dir: key === "model" ? 1 : -1 };
    renderRun();
  }));
  $("board-foot").innerHTML = ranked
    ? "Click a column to sort. Technical fails sink to the bottom unranked. ★ = current writer. Three scripts per model is triage, not a ranking; scores compare only within one benchmark version."
    : "Click a column to sort. This run has no V1 score, so there is no rank. ★ = current writer.";
}

function renderFails() {
  const rows = [];
  for (const run of LB.runs) for (const r of run.rows) if (r.technical_fail) rows.push([run, r]);
  $("fails").innerHTML = "<thead><tr><th>model</th><th>run</th><th>why</th></tr></thead><tbody>" +
    (rows.length ? rows.map(([run, r]) => `<tr class="fail"><td class="model">${esc(r.model)}</td><td>${esc(run.run_id)}</td>
      <td class="notes">${esc(r.notes || r.exclusion || (run.kind === "censorship" ? "censorship (refined reading)" : "technical fail"))}</td></tr>`).join("")
      : '<tr><td colspan="3" class="muted">None.</td></tr>') + "</tbody>";
  const render = () => {
    const q = $("excl-filter").value.trim().toLowerCase();
    const items = Object.entries(LB.exclusions || {}).filter(([k, v]) => !q || k.toLowerCase().includes(q) || v.toLowerCase().includes(q));
    $("exclusions").innerHTML = "<thead><tr><th>model or family</th><th>reason</th></tr></thead><tbody>" +
      items.map(([k, v]) => `<tr><td class="model">${esc(k)}</td><td class="notes">${esc(v)}</td></tr>`).join("") + "</tbody>";
  };
  $("excl-filter").addEventListener("input", render);
  render();
}

function renderInformal(data) {
  const entries = (data && data.entries) || [];
  if (!entries.length) { $("informal").innerHTML = '<p class="muted">No entries yet.</p>'; return; }
  $("informal").innerHTML = entries.map((e) => {
    const eps = (e.episodes || []).map((ep) =>
      `<li><span class="model">${esc(ep.model)}</span>: <a href="${SITE}/episode/${encodeURIComponent(ep.slug)}/">#${esc(ep.episode_number)} ${esc(ep.slug)}</a>
        <span class="chip">${esc(ep.written)}</span>${ep.note ? ` <span class="muted small">${esc(ep.note)}</span>` : ""}</li>`).join("");
    const costs = Object.entries(e.cost_per_script || {}).map(([m, c]) => `<span class="chip">${esc(m)} ~$${Number(c).toFixed(2)}/script</span>`).join(" ");
    const imps = Object.entries(e.impressions || {}).map(([m, t]) => `<li><b>${esc(m)}</b>: ${esc(t)}</li>`).join("");
    return `<article class="card entry">
      <h3>${esc(e.date)}${e.title ? ": " + esc(e.title) : ""}</h3>
      <p class="small muted">Judge: ${esc(e.judge)}. Models: ${(e.models || []).map(esc).join(", ")}</p>
      <details><summary>Episodes read (${(e.episodes || []).length})</summary><ul>${eps}</ul>
        ${e.caveats ? `<p class="small muted">${esc(e.caveats)}</p>` : ""}</details>
      ${costs ? `<p class="small">${costs}${e.cost_basis ? ` <span class="muted">(${esc(e.cost_basis.source || "")}, ${esc(e.cost_basis.mix || "")})</span>` : ""}</p>` : ""}
      <ul>${imps}${e.impressions_all_models ? `<li><b>all models</b>: ${esc(e.impressions_all_models)}</li>` : ""}</ul>
      ${e.daniel ? `<blockquote>“${esc(e.daniel)}” <span class="muted small">(Daniel)</span></blockquote>` : ""}
      ${e.verdict ? `<div class="verdict"><b>Verdict.</b> ${esc(e.verdict)}</div>` : ""}
    </article>`;
  }).join("");
}

async function main() {
  try {
    LB = await getJSON("leaderboard.json");
    $("generated").textContent = `Leaderboard generated ${LB.generated}; benchmark ${LB.benchmark_version}.`;
    renderCurrent();
    renderPicker();
    renderRun();
    renderFails();
  } catch (err) {
    $("current").innerHTML = `<p class="error">Couldn't load leaderboard.json (${esc(err.message)}).</p>`;
  }
  try {
    renderInformal(await getJSON("informal-evaluations.json"));
  } catch (err) {
    $("informal").innerHTML = `<p class="error">Couldn't load informal-evaluations.json (${esc(err.message)}).</p>`;
  }
}

main();
