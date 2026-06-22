const PUBLIC = "public";

const TYPE_LABELS = { cycle: "周期", growth: "成长", event: "事件", unknown: "未分类" };
const TREND_LABELS = { up: "上涨", range: "震荡", down: "下跌" };
const ACTION_LABELS = { hold: "持有", add: "加仓", reduce: "减仓", exit: "清仓" };

let summary = null;
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
    if (btn.dataset.tab === "review") renderReviewList();
  });
});

async function init() {
  summary = await loadJson(`${PUBLIC}/summary.json`);
  reviewsIndex = await loadJson(`${PUBLIC}/reviews_index.json`);

  if (summary.generated_at) {
    document.getElementById("generated-at").textContent =
      `更新于 ${new Date(summary.generated_at).toLocaleString("zh-CN")} · 公开摘要`;
  }

  if (summary.flash_note_url) {
    document.getElementById("flash-note-link").href = summary.flash_note_url;
  }

  renderDashboard();
  renderReviewList();
}

function renderDashboard() {
  const p = summary.portfolio;
  document.getElementById("dashboard-cards").innerHTML = `
    <div class="stat-card"><div class="num">${p.position_count}</div><div class="label">持仓数</div></div>
    <div class="stat-card"><div class="num">${p.avg_return_pct}%</div><div class="label">平均浮盈</div></div>
    <div class="stat-card"><div class="num">${p.thesis_count}</div><div class="label">逻辑卡片</div></div>
    <div class="stat-card"><div class="num">${summary.discipline.alert_count}</div><div class="label">纪律提醒</div></div>
  `;

  const typeText = Object.entries(p.by_stock_type || {})
    .map(([k, v]) => `${TYPE_LABELS[k] || k} ${v}`)
    .join(" · ");

  const decEl = document.getElementById("dashboard-decisions");
  if (!summary.decisions.length) {
    decEl.innerHTML = `<div class="item-card">暂无决策摘要</div>`;
  } else {
    decEl.innerHTML = `<div class="item-card item-meta">类型分布：${typeText || "—"}</div>` +
      summary.decisions.map((d) => {
        const cls = d.action === "exit" ? "critical" : d.action === "hold" ? "hold" : "high";
        return `<div class="item-card">
          <div class="item-title">${d.label}
            <span class="tag">${TYPE_LABELS[d.stock_type] || d.stock_type}</span>
            <span class="tag ${cls}">${ACTION_LABELS[d.action]}${d.reduce_pct ? " " + d.reduce_pct + "%" : ""}</span>
          </div>
          <div class="item-meta">
            浮盈 ${d.return_pct ?? "—"}% · 趋势 ${TREND_LABELS[d.trend] || d.trend || "—"}<br>
            ${d.trigger_summary}
          </div>
        </div>`;
      }).join("");
  }

  const disc = summary.discipline;
  const sev = disc.severity === "critical" ? "alert-box" : "item-card";
  document.getElementById("dashboard-discipline").innerHTML =
    `<div class="${sev}">${disc.summary}${disc.rule_names?.length ? "<br><small>规则：" + disc.rule_names.join(", ") + "</small>" : ""}</div>`;
}

function renderReviewList() {
  const el = document.getElementById("review-list");
  const out = document.getElementById("review-output");
  out.classList.add("hidden");

  if (!reviewsIndex.length) {
    el.innerHTML = `<div class="item-card">暂无复盘。工作日 Actions 会自动生成。</div>`;
    return;
  }

  el.innerHTML = reviewsIndex.map((r) => `
    <div class="item-card review-item" data-path="${r.path}">
      <div class="item-title">${r.date} 复盘</div>
      <div class="item-meta">点击查看（可能含代码，无成本明细）</div>
    </div>
  `).join("");

  el.querySelectorAll(".review-item").forEach((node) => {
    node.addEventListener("click", () => showReview(node.dataset.path));
  });
}

async function showReview(path) {
  const text = await loadText(path);
  const out = document.getElementById("review-output");
  out.textContent = text;
  out.classList.remove("hidden");
  out.scrollIntoView({ behavior: "smooth" });
}

init().catch((err) => {
  document.body.insertAdjacentHTML(
    "afterbegin",
    `<div class="alert-box" style="margin:12px">加载失败：${err.message}</div>`
  );
});
