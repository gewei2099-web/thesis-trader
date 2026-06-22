const DATA = "data";

const TYPE_LABELS = { cycle: "周期", growth: "成长", event: "事件" };
const TREND_LABELS = { up: "上涨", range: "震荡", down: "下跌" };
const ACTION_LABELS = { hold: "持有", add: "加仓", reduce: "减仓", exit: "清仓" };
const THESIS_STATUS_LABELS = { valid: "有效", weakening: "弱化", invalid: "失效" };

let watchlist = { items: [] };
let positions = { items: [] };
let thesisItems = [];
let snapshot = { decisions: [], alerts: [], generated_at: "" };
let disciplineLog = { entries: [] };
let reviewsIndex = [];

async function loadJson(path) {
  const url = new URL(path, document.baseURI).href;
  const res = await fetch(url, { cache: "no-cache" });
  if (!res.ok) throw new Error(`无法加载 ${url}`);
  return res.json();
}

async function loadText(path) {
  const url = new URL(path, document.baseURI).href;
  const res = await fetch(url, { cache: "no-cache" });
  if (!res.ok) throw new Error(`无法加载 ${url}`);
  return res.text();
}

function switchTab(tab) {
  document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
  document.querySelectorAll(".bottom-nav button").forEach((b) => b.classList.remove("active"));
  document.getElementById(`panel-${tab}`).classList.add("active");
  document.querySelector(`.bottom-nav button[data-tab="${tab}"]`).classList.add("active");
}

document.querySelectorAll(".bottom-nav button").forEach((btn) => {
  btn.addEventListener("click", () => {
    switchTab(btn.dataset.tab);
    refreshTab(btn.dataset.tab);
  });
});

function refreshTab(tab) {
  if (tab === "dashboard") renderDashboard();
  if (tab === "watchlist") renderWatchlist();
  if (tab === "positions") renderPositions();
  if (tab === "thesis") renderThesis();
  if (tab === "review") renderReviewList();
  if (tab === "discipline") renderDiscipline();
}

async function init() {
  watchlist = await loadJson(`${DATA}/watchlist.json`);
  positions = await loadJson(`${DATA}/positions.json`);
  snapshot = await loadJson(`${DATA}/snapshot.json`);
  disciplineLog = await loadJson(`${DATA}/discipline_log.json`);
  reviewsIndex = await loadJson(`${DATA}/reviews_index.json`);

  const symbols = await loadJson(`${DATA}/thesis_index.json`);
  thesisItems = [];
  for (const sym of symbols) {
    thesisItems.push(await loadJson(`${DATA}/thesis/${sym}.json`));
  }

  if (snapshot.generated_at) {
    const t = new Date(snapshot.generated_at);
    document.getElementById("generated-at").textContent =
      `更新于 ${t.toLocaleString("zh-CN")} · 只读`;
  }

  renderDashboard();
  renderWatchlist();
  renderPositions();
  renderThesis();
  renderReviewList();
  renderDiscipline();
}

function renderDashboard() {
  const cards = document.getElementById("dashboard-cards");
  cards.innerHTML = `
    <div class="stat-card"><div class="num">${positions.items.length}</div><div class="label">持仓</div></div>
    <div class="stat-card"><div class="num">${watchlist.items.length}</div><div class="label">股票池</div></div>
    <div class="stat-card"><div class="num">${thesisItems.length}</div><div class="label">逻辑卡片</div></div>
    <div class="stat-card"><div class="num">${snapshot.alerts.length}</div><div class="label">纪律提醒</div></div>
  `;

  const el = document.getElementById("dashboard-alerts");
  if (!snapshot.decisions.length) {
    el.innerHTML = `<div class="item-card">暂无决策数据</div>`;
    return;
  }

  let html = snapshot.decisions.map((d) => {
    const cls = d.action === "exit" ? "critical" : d.action === "hold" ? "hold" : "high";
    return `<div class="item-card">
      <div class="item-title">${d.name || d.symbol}
        <span class="tag ${cls}">${ACTION_LABELS[d.action]}${d.reduce_pct ? " " + d.reduce_pct + "%" : ""}</span>
      </div>
      <div class="item-meta">${d.rationale}</div>
    </div>`;
  }).join("");

  if (snapshot.alerts.length) {
    html += `<h3 style="margin-top:16px;font-size:0.9rem;">纪律提醒</h3>`;
    html += snapshot.alerts.map((a) =>
      `<div class="alert-box">${a.message}<br><small>${a.risk_if_ignored}</small></div>`
    ).join("");
  }
  el.innerHTML = html;
}

function renderWatchlist() {
  const el = document.getElementById("watchlist-list");
  if (!watchlist.items.length) {
    el.innerHTML = `<div class="item-card">股票池为空</div>`;
    return;
  }
  el.innerHTML = watchlist.items.map((w) => `
    <div class="item-card">
      <div class="item-title">${w.name} (${w.symbol})</div>
      <div class="item-meta">
        <span class="tag">${TYPE_LABELS[w.stock_type] || w.stock_type}</span>
        ${w.added_reason || ""}
      </div>
    </div>
  `).join("");
}

function renderPositions() {
  const el = document.getElementById("positions-list");
  if (!positions.items.length) {
    el.innerHTML = `<div class="item-card">暂无持仓</div>`;
    return;
  }
  el.innerHTML = positions.items.map((p) => {
    const ret = (((p.current_price - p.avg_cost) / p.avg_cost) * 100).toFixed(2);
    return `
    <div class="item-card">
      <div class="item-title">${p.name || p.symbol} (${p.symbol})</div>
      <div class="item-meta">
        成本 ${p.avg_cost} → 现价 ${p.current_price}，浮盈 <strong>${ret}%</strong><br>
        趋势 ${TREND_LABELS[p.trend]} · 基本面 ${p.fundamental_state} · 情绪 ${p.market_sentiment}
      </div>
    </div>`;
  }).join("");
}

function renderThesis() {
  const el = document.getElementById("thesis-list");
  if (!thesisItems.length) {
    el.innerHTML = `<div class="item-card">暂无逻辑卡片</div>`;
    return;
  }
  el.innerHTML = thesisItems.map((t) => `
    <div class="item-card">
      <div class="item-title">${t.name || t.symbol} (${t.symbol})</div>
      <div class="item-meta">
        <span class="tag">${TYPE_LABELS[t.thesis_type]}</span>
        <span class="tag">${THESIS_STATUS_LABELS[t.thesis_status] || t.thesis_status}</span><br>
        ${t.core_thesis}
      </div>
    </div>
  `).join("");
}

function renderReviewList() {
  const el = document.getElementById("review-list");
  const out = document.getElementById("review-output");
  out.classList.add("hidden");

  if (!reviewsIndex.length) {
    el.innerHTML = `<div class="item-card">暂无复盘记录。GitHub Actions 每日会自动生成。</div>`;
    return;
  }

  el.innerHTML = reviewsIndex.map((r) => `
    <div class="item-card" style="cursor:pointer" onclick="showReview('${r.path}')">
      <div class="item-title">${r.date} 复盘</div>
      <div class="item-meta">点击查看详情</div>
    </div>
  `).join("");
}

async function showReview(path) {
  const text = await loadText(path);
  const out = document.getElementById("review-output");
  out.textContent = text;
  out.classList.remove("hidden");
  out.scrollIntoView({ behavior: "smooth" });
}

function renderDiscipline() {
  const el = document.getElementById("discipline-list");
  const entries = [...disciplineLog.entries].reverse();
  if (!entries.length) {
    el.innerHTML = `<div class="item-card">暂无纪律记录</div>`;
    return;
  }
  el.innerHTML = entries.map((e) => `
    <div class="item-card ${e.acknowledged ? "" : "alert-box"}">
      <div class="item-title">${e.symbol} · ${e.rule_name}</div>
      <div class="item-meta">${e.alert_message}</div>
      <div class="item-meta">${e.created_at} · ${ACTION_LABELS[e.required_action]} ${e.reduce_pct ? e.reduce_pct + "%" : ""}</div>
      ${e.acknowledged ? `<span class="tag hold">已确认</span>` : `<span class="tag high">待处理</span>`}
      ${e.defer_reason ? `<div class="item-meta">暂缓：${e.defer_reason}</div>` : ""}
    </div>
  `).join("");
}

init().catch((err) => {
  document.body.insertAdjacentHTML(
    "afterbegin",
    `<div class="alert-box" style="margin:12px">加载失败：${err.message}<br><small>当前地址：${location.href}</small></div>`
  );
});

window.showReview = showReview;
