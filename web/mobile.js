const STORAGE_KEY = "thesis-trader-mobile-v1";

const TREND_LABELS = { up: "上涨", range: "震荡", down: "下跌" };

let state = { version: 1, positions: [], updated_at: null };

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) state = JSON.parse(raw);
  } catch (e) {
    console.warn(e);
  }
}

function saveState() {
  state.updated_at = new Date().toISOString();
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  document.getElementById("save-status").textContent =
    `已自动保存 ${new Date().toLocaleString("zh-CN")} · 仅本机`;
}

function switchTab(tab) {
  document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
  document.querySelectorAll(".mobile-nav button").forEach((b) => b.classList.remove("active"));
  document.getElementById(`panel-${tab}`).classList.add("active");
  document.querySelector(`.mobile-nav button[data-tab="${tab}"]`).classList.add("active");
}

document.querySelectorAll(".mobile-nav button").forEach((btn) => {
  btn.addEventListener("click", () => switchTab(btn.dataset.tab));
});

function renderPositions() {
  const el = document.getElementById("positions-list");
  if (!state.positions.length) {
    el.innerHTML = `<div class="item-card">暂无持仓，点下方添加</div>`;
    return;
  }
  el.innerHTML = state.positions
    .map((p, i) => {
      const ret = (((p.current_price - p.avg_cost) / p.avg_cost) * 100).toFixed(2);
      return `<div class="item-card">
        <div class="item-title">${p.name || p.symbol} (${p.symbol})</div>
        <div class="item-meta">
          ${p.shares} 股 · 成本 ${p.avg_cost} · 现价 ${p.current_price}<br>
          浮盈 <strong>${ret}%</strong> · ${TREND_LABELS[p.trend] || p.trend}
        </div>
        <div class="row-actions">
          <button class="btn small" type="button" data-edit="${i}">编辑</button>
          <button class="btn small" type="button" data-del="${i}">删除</button>
        </div>
      </div>`;
    })
    .join("");

  el.querySelectorAll("[data-edit]").forEach((btn) => {
    btn.addEventListener("click", () => showForm(state.positions[+btn.dataset.edit], +btn.dataset.edit));
  });
  el.querySelectorAll("[data-del]").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (confirm("删除这条持仓？")) {
        state.positions.splice(+btn.dataset.del, 1);
        saveState();
        renderPositions();
      }
    });
  });
}

function showForm(existing, idx) {
  const p = existing || {};
  const el = document.getElementById("position-form");
  el.classList.remove("hidden");
  el.innerHTML = `
    <label>代码</label><input id="f-symbol" value="${p.symbol || ""}" />
    <label>名称</label><input id="f-name" value="${p.name || ""}" />
    <label>股数</label><input id="f-shares" type="number" inputmode="decimal" value="${p.shares ?? ""}" />
    <label>成本价</label><input id="f-cost" type="number" step="0.01" inputmode="decimal" value="${p.avg_cost ?? ""}" />
    <label>现价</label><input id="f-price" type="number" step="0.01" inputmode="decimal" value="${p.current_price ?? ""}" />
    <label>趋势</label>
    <select id="f-trend">
      <option value="up">上涨</option><option value="range">震荡</option><option value="down">下跌</option>
    </select>
    <label>基本面</label>
    <select id="f-fund">
      <option value="strengthened">强化</option><option value="unchanged">不变</option><option value="weakened">弱化</option>
    </select>
    <label>市场情绪</label>
    <select id="f-sent">
      <option value="low">低</option><option value="medium">中</option><option value="high">高</option>
    </select>
    <button class="btn primary" type="button" id="f-save">保存</button>
    <button class="btn" type="button" id="f-cancel">取消</button>
  `;
  if (p.trend) document.getElementById("f-trend").value = p.trend;
  if (p.fundamental_state) document.getElementById("f-fund").value = p.fundamental_state;
  if (p.market_sentiment) document.getElementById("f-sent").value = p.market_sentiment;

  document.getElementById("f-save").onclick = () => {
    const item = {
      symbol: document.getElementById("f-symbol").value.trim(),
      name: document.getElementById("f-name").value.trim(),
      shares: parseFloat(document.getElementById("f-shares").value),
      avg_cost: parseFloat(document.getElementById("f-cost").value),
      current_price: parseFloat(document.getElementById("f-price").value),
      trend: document.getElementById("f-trend").value,
      fundamental_state: document.getElementById("f-fund").value,
      market_sentiment: document.getElementById("f-sent").value,
      opened_at: p.opened_at || new Date().toISOString().slice(0, 10),
      notes: p.notes || "",
    };
    if (!item.symbol || !item.shares || !item.avg_cost || !item.current_price) {
      alert("请填写代码、股数、成本、现价");
      return;
    }
    if (idx >= 0) state.positions[idx] = item;
    else state.positions.push(item);
    saveState();
    el.classList.add("hidden");
    renderPositions();
  };
  document.getElementById("f-cancel").onclick = () => el.classList.add("hidden");
}

document.getElementById("btn-add").onclick = () => showForm(null, -1);

function exportPayload() {
  return JSON.stringify({ version: 1, positions: state.positions, updated_at: state.updated_at }, null, 2);
}

document.getElementById("btn-export").onclick = async () => {
  const text = exportPayload();
  try {
    await navigator.clipboard.writeText(text);
    alert("已复制到剪贴板，回家粘贴到电脑「同步」页");
  } catch {
    document.getElementById("import-json").value = text;
    switchTab("sync");
    alert("无法自动复制，JSON 已填入下方文本框，请手动全选复制");
  }
};

document.getElementById("btn-download").onclick = () => {
  const blob = new Blob([exportPayload()], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `thesis-trader-${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
};

document.getElementById("btn-import").onclick = () => {
  try {
    const data = JSON.parse(document.getElementById("import-json").value);
    if (!data.positions) throw new Error("缺少 positions");
    state.positions = data.positions;
    saveState();
    renderPositions();
    alert("已恢复到本手机");
  } catch (e) {
    alert("导入失败：" + e.message);
  }
};

loadState();
renderPositions();
