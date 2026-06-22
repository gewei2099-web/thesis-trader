const API = "";

const TYPE_LABELS = { cycle: "周期", growth: "成长", event: "事件" };
const TREND_LABELS = { up: "上涨", range: "震荡", down: "下跌" };
const ACTION_LABELS = { hold: "持有", add: "加仓", reduce: "减仓", exit: "清仓" };
const THESIS_STATUS_LABELS = { valid: "有效", weakening: "弱化", invalid: "失效" };

let watchlist = { items: [] };
let positions = { items: [] };
let thesisItems = [];

async function api(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || res.statusText);
  }
  return res.json();
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
    refreshCurrentTab(btn.dataset.tab);
  });
});

function refreshCurrentTab(tab) {
  if (tab === "dashboard") loadDecisions();
  if (tab === "watchlist") renderWatchlist();
  if (tab === "positions") renderPositions();
  if (tab === "thesis") renderThesis();
  if (tab === "discipline") loadDiscipline();
  if (tab === "rules") loadRules();
  if (tab === "sync") document.getElementById("sync-msg").textContent = "";
}

async function init() {
  watchlist = await api("/api/watchlist");
  positions = await api("/api/positions");
  const t = await api("/api/thesis");
  thesisItems = t.items || [];
  await loadDecisions();
  renderWatchlist();
  renderPositions();
  renderThesis();
}

async function loadDecisions() {
  const data = await api("/api/decisions");
  const cards = document.getElementById("dashboard-cards");
  cards.innerHTML = `
    <div class="card stat-card"><div class="num">${positions.items.length}</div><div class="label">持仓</div></div>
    <div class="card stat-card"><div class="num">${watchlist.items.length}</div><div class="label">股票池</div></div>
    <div class="card stat-card"><div class="num">${thesisItems.length}</div><div class="label">逻辑卡片</div></div>
    <div class="card stat-card"><div class="num">${data.alerts.length}</div><div class="label">纪律提醒</div></div>
  `;

  const alertsEl = document.getElementById("dashboard-alerts");
  if (!data.decisions.length) {
    alertsEl.innerHTML = `<div class="item-card">暂无持仓决策。请先添加持仓与逻辑卡片。</div>`;
    return;
  }

  let html = data.decisions.map((d) => {
    const cls = d.action === "exit" ? "critical" : d.action === "hold" ? "hold" : "high";
    return `<div class="item-card">
      <div class="item-title">${d.name || d.symbol} <span class="tag ${cls}">${ACTION_LABELS[d.action] || d.action}${d.reduce_pct ? " " + d.reduce_pct + "%" : ""}</span></div>
      <div class="item-meta">${d.rationale}</div>
    </div>`;
  }).join("");

  if (data.alerts.length) {
    html += `<h3 style="margin-top:16px;font-size:0.9rem;">纪律提醒</h3>`;
    html += data.alerts.map((a) => `<div class="alert-box">${a.message}<br><small>${a.risk_if_ignored}</small></div>`).join("");
  }
  alertsEl.innerHTML = html;
}

function renderWatchlist() {
  const el = document.getElementById("watchlist-list");
  if (!watchlist.items.length) {
    el.innerHTML = `<div class="item-card">股票池为空</div>`;
    return;
  }
  el.innerHTML = watchlist.items.map((w, i) => `
    <div class="item-card">
      <div class="item-title">${w.name} (${w.symbol})</div>
      <div class="item-meta">
        <span class="tag">${TYPE_LABELS[w.stock_type] || w.stock_type}</span>
        <span class="tag">${w.status}</span><br>
        ${w.added_reason || ""}
      </div>
      <div class="row-actions">
        <button class="btn small" onclick="removeWatchItem(${i})">移除</button>
      </div>
    </div>
  `).join("");
}

function showWatchForm() {
  const el = document.getElementById("watch-form");
  el.classList.remove("hidden");
  el.innerHTML = `
    <label>代码</label><input id="w-symbol" placeholder="002738" />
    <label>名称</label><input id="w-name" placeholder="中矿资源" />
    <label>类型</label>
    <select id="w-type"><option value="cycle">周期</option><option value="growth">成长</option><option value="event">事件</option></select>
    <label>加入原因</label><input id="w-reason" />
    <button class="btn primary" onclick="saveWatchItem()">保存</button>
  `;
}

async function saveWatchItem() {
  watchlist.items.push({
    symbol: document.getElementById("w-symbol").value.trim(),
    name: document.getElementById("w-name").value.trim(),
    stock_type: document.getElementById("w-type").value,
    status: "watching",
    added_reason: document.getElementById("w-reason").value.trim(),
    added_at: new Date().toISOString().slice(0, 10),
    notes: "",
  });
  await api("/api/watchlist", { method: "POST", body: JSON.stringify(watchlist) });
  document.getElementById("watch-form").classList.add("hidden");
  renderWatchlist();
}

async function removeWatchItem(index) {
  watchlist.items.splice(index, 1);
  await api("/api/watchlist", { method: "POST", body: JSON.stringify(watchlist) });
  renderWatchlist();
}

function renderPositions() {
  const el = document.getElementById("positions-list");
  if (!positions.items.length) {
    el.innerHTML = `<div class="item-card">暂无持仓</div>`;
    return;
  }
  el.innerHTML = positions.items.map((p, i) => `
    <div class="item-card">
      <div class="item-title">${p.name || p.symbol} (${p.symbol})</div>
      <div class="item-meta">
        成本 ${p.avg_cost} → 现价 ${p.current_price}，
        浮盈 <strong>${(((p.current_price - p.avg_cost) / p.avg_cost) * 100).toFixed(2)}%</strong><br>
        趋势 ${TREND_LABELS[p.trend]} · 基本面 ${p.fundamental_state} · 情绪 ${p.market_sentiment}
      </div>
      <div class="row-actions">
        <button class="btn small" onclick="editPosition(${i})">编辑</button>
        <button class="btn small" onclick="removePosition(${i})">删除</button>
      </div>
    </div>
  `).join("");
}

function showPositionForm(existing) {
  const p = existing || {};
  const el = document.getElementById("position-form");
  el.classList.remove("hidden");
  el.innerHTML = `
    <label>代码</label><input id="p-symbol" value="${p.symbol || ""}" />
    <label>名称</label><input id="p-name" value="${p.name || ""}" />
    <label>股数</label><input id="p-shares" type="number" value="${p.shares || ""}" />
    <label>成本价</label><input id="p-cost" type="number" step="0.01" value="${p.avg_cost || ""}" />
    <label>现价</label><input id="p-price" type="number" step="0.01" value="${p.current_price || ""}" />
    <label>趋势</label>
    <select id="p-trend">
      <option value="up" ${p.trend === "up" ? "selected" : ""}>上涨</option>
      <option value="range" ${p.trend === "range" ? "selected" : ""}>震荡</option>
      <option value="down" ${p.trend === "down" ? "selected" : ""}>下跌</option>
    </select>
    <label>基本面</label>
    <select id="p-fund">
      <option value="strengthened">强化</option>
      <option value="unchanged" selected>不变</option>
      <option value="weakened">弱化</option>
    </select>
    <label>市场情绪</label>
    <select id="p-sent">
      <option value="low">低</option>
      <option value="medium" selected>中</option>
      <option value="high">高</option>
    </select>
    <button class="btn primary" onclick="savePosition(${existing ? existing._idx : -1})">保存</button>
  `;
  if (p.fundamental_state) document.getElementById("p-fund").value = p.fundamental_state;
  if (p.market_sentiment) document.getElementById("p-sent").value = p.market_sentiment;
}

function editPosition(i) {
  showPositionForm({ ...positions.items[i], _idx: i });
}

async function savePosition(idx) {
  const item = {
    symbol: document.getElementById("p-symbol").value.trim(),
    name: document.getElementById("p-name").value.trim(),
    shares: parseFloat(document.getElementById("p-shares").value),
    avg_cost: parseFloat(document.getElementById("p-cost").value),
    current_price: parseFloat(document.getElementById("p-price").value),
    trend: document.getElementById("p-trend").value,
    fundamental_state: document.getElementById("p-fund").value,
    market_sentiment: document.getElementById("p-sent").value,
    opened_at: new Date().toISOString().slice(0, 10),
    notes: "",
  };
  if (idx >= 0) positions.items[idx] = item;
  else positions.items.push(item);
  await api("/api/positions", { method: "POST", body: JSON.stringify(positions) });
  document.getElementById("position-form").classList.add("hidden");
  renderPositions();
  loadDecisions();
}

async function removePosition(i) {
  positions.items.splice(i, 1);
  await api("/api/positions", { method: "POST", body: JSON.stringify(positions) });
  renderPositions();
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
      <div class="row-actions">
        <button class="btn small" onclick='editThesis(${JSON.stringify(t).replace(/'/g, "&#39;")})'>编辑</button>
      </div>
    </div>
  `).join("");
}

function showThesisForm(existing) {
  const t = existing || { thesis_type: "cycle", thesis_status: "valid", key_metrics: [], invalidation_conditions: [""] };
  const el = document.getElementById("thesis-form");
  el.classList.remove("hidden");
  el.innerHTML = `
    <label>代码</label><input id="t-symbol" value="${t.symbol || ""}" ${t.symbol ? "readonly" : ""} />
    <label>名称</label><input id="t-name" value="${t.name || ""}" />
    <label>核心逻辑</label><textarea id="t-core">${t.core_thesis || ""}</textarea>
    <label>类型</label>
    <select id="t-type">
      <option value="cycle">周期</option><option value="growth">成长</option><option value="event">事件</option>
    </select>
    <label>逻辑状态</label>
    <select id="t-status">
      <option value="valid">有效</option><option value="weakening">弱化</option><option value="invalid">失效</option>
    </select>
    <label>失效条件（每行一条）</label>
    <textarea id="t-invalidate">${(t.invalidation_conditions || [""]).join("\n")}</textarea>
    <label>预期结果</label><input id="t-outcome" value="${t.expected_outcome || ""}" />
    <button class="btn primary" onclick="saveThesis()">保存</button>
  `;
  if (t.thesis_type) document.getElementById("t-type").value = t.thesis_type;
  if (t.thesis_status) document.getElementById("t-status").value = t.thesis_status;
}

function editThesis(t) {
  showThesisForm(t);
}

async function saveThesis() {
  const card = {
    symbol: document.getElementById("t-symbol").value.trim(),
    name: document.getElementById("t-name").value.trim(),
    core_thesis: document.getElementById("t-core").value.trim(),
    thesis_type: document.getElementById("t-type").value,
    thesis_status: document.getElementById("t-status").value,
    key_metrics: [],
    invalidation_conditions: document.getElementById("t-invalidate").value.split("\n").map(s => s.trim()).filter(Boolean),
    expected_outcome: document.getElementById("t-outcome").value.trim(),
    last_reviewed: new Date().toISOString().slice(0, 10),
    notes: "",
  };
  await api("/api/thesis", { method: "POST", body: JSON.stringify(card) });
  const t = await api("/api/thesis");
  thesisItems = t.items || [];
  document.getElementById("thesis-form").classList.add("hidden");
  renderThesis();
  loadDecisions();
}

async function runReview() {
  const info = document.getElementById("market-info").value;
  const data = await api("/api/review", { method: "POST", body: JSON.stringify({ market_info: info }) });
  document.getElementById("review-output").textContent = data.markdown;
  loadDiscipline();
}

async function loadDiscipline() {
  const data = await api("/api/discipline");
  const el = document.getElementById("discipline-list");
  if (!data.entries.length) {
    el.innerHTML = `<div class="item-card">暂无纪律记录。触发减仓/清仓规则后会出现在此。</div>`;
    return;
  }
  el.innerHTML = data.entries.slice().reverse().map((e) => `
    <div class="item-card ${e.acknowledged ? "" : "alert-box"}">
      <div class="item-title">${e.symbol} · ${e.rule_name}</div>
      <div class="item-meta">${e.alert_message}</div>
      <div class="item-meta">${e.created_at} · ${ACTION_LABELS[e.required_action]} ${e.reduce_pct ? e.reduce_pct + "%" : ""}</div>
      ${e.acknowledged ? `<div class="tag hold">已确认</div>` : `
        <div class="row-actions">
          <button class="btn small primary" onclick="ackDiscipline('${e.id}', true)">已执行</button>
          <button class="btn small" onclick="deferDiscipline('${e.id}')">暂缓</button>
        </div>`}
      ${e.defer_reason ? `<div class="item-meta">暂缓原因：${e.defer_reason}</div>` : ""}
    </div>
  `).join("");
}

async function ackDiscipline(id, ok) {
  await api("/api/discipline/ack", { method: "POST", body: JSON.stringify({ entry_id: id, acknowledged: ok }) });
  loadDiscipline();
}

async function deferDiscipline(id) {
  const reason = prompt("暂缓原因（必填）：");
  if (!reason) return;
  await api("/api/discipline/ack", { method: "POST", body: JSON.stringify({ entry_id: id, acknowledged: false, defer_reason: reason }) });
  loadDiscipline();
}

async function loadRules() {
  const data = await api("/api/rules");
  document.getElementById("rules-json").value = JSON.stringify(data, null, 2);
  document.getElementById("rules-msg").textContent = "";
}

async function saveRules() {
  try {
    const payload = JSON.parse(document.getElementById("rules-json").value);
    await api("/api/rules", { method: "POST", body: JSON.stringify(payload) });
    document.getElementById("rules-msg").textContent = "已保存，决策引擎将使用新规则。";
    loadDecisions();
  } catch (e) {
    document.getElementById("rules-msg").textContent = "保存失败：" + e.message;
  }
}

async function importFromPhone() {
  try {
    const payload = JSON.parse(document.getElementById("sync-json").value);
    const res = await api("/api/import-local", { method: "POST", body: JSON.stringify({ payload }) });
    document.getElementById("sync-msg").textContent = `已导入 ${res.positions} 条持仓到电脑本地。`;
    renderPositions();
    loadDecisions();
  } catch (e) {
    document.getElementById("sync-msg").textContent = "导入失败：" + e.message;
  }
}

init().catch((err) => alert("加载失败：" + err.message));
