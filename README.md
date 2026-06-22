# thesis-trader

个人交易决策辅助系统。

## 本地使用（完整数据 · 可编辑）

```powershell
cd D:\Projects\thesis-trader
.\setup.ps1
.\run.bat
```

访问 **http://localhost:8765** — 含持仓成本、逻辑卡片、规则配置、纪律确认。

## 方案 A：公开仓库 + 本地真实数据

仓库保持 **Public**，GitHub Pages 只展示摘要（无真实成本）。

### 真实成本/股数存哪里？

| 文件 | 是否提交 Git | 内容 |
|------|-------------|------|
| `data/positions.json` | ✅ 提交 | 占位数据（股数 100、成本=现价），供 Actions 更新收盘价 |
| `data/local/private.json` | ❌ 不提交 | **真实**股数、成本、备注 |

本地 Web 保存持仓时：
1. 真实数据写入 `data/local/private.json`（自动）
2. 占位数据写入 `data/positions.json`（推送远端）

`git pull` 后 Actions 更新的**现价**会合并进来，**真实成本/股数不会被覆盖**。

### 首次填写真实持仓

```powershell
# 方式 1：本地 Web 编辑持仓并保存一次
.\run.bat

# 方式 2：复制示例后改数字
copy data\local\private.json.example data\local\private.json
```

## 手机本地改持仓（不上传 GitHub）

任意地点用手机，**无需电脑开机**：

1. 打开（可「添加到主屏幕」）  
   **https://gewei2099-web.github.io/thesis-trader/mobile.html**
2. 编辑持仓 → **自动保存在本手机**（localStorage）
3. 数据**不会**上传到 GitHub

回家同步到电脑：

1. 手机 → **同步** → **导出 JSON**（复制到剪贴板）
2. 电脑 `run.bat` → **同步** 页 → 粘贴 → **从手机导入**
3. 真实成本写入 `private.json`，决策引擎在电脑上完整运行

## 手机公开页（摘要 · 无敏感数据）

**https://gewei2099-web.github.io/thesis-trader/**

Pages 仅发布：
- `public/summary.json` — 持仓数、平均浮盈、匿名决策摘要
- `reports/*.md` — 复盘报告
- **速记按钮** — 跳转 GitHub Issue 记录盘中想法

完整 `data/` 不在 Pages 上展示；`positions.json` 在 Git 上仅为占位值。

## 自动化（GitHub Actions）

| 工作流 | 时间 | 作用 |
|--------|------|------|
| Fetch Closing Prices | 工作日 15:30 | akshare 更新收盘价 |
| Daily Review | 工作日 21:00 | 复盘 + 飞书纪律推送 + 构建 Pages |
| Build Pages | push 后 | 重建公开站点 |

### Secrets（Settings → Secrets → Actions）

| Secret | 用途 |
|--------|------|
| `FEISHU_WEBHOOK_URL` | 纪律触发时飞书机器人推送 |
| `MARKET_INFO` | 定时复盘可选市场信息（可留空） |

### 飞书机器人

1. 飞书群 → 设置 → 群机器人 → 自定义机器人 → 复制 Webhook
2. 填入 GitHub Secret `FEISHU_WEBHOOK_URL`

## 规则配置

编辑 `data/config/rules.json`，或本地 Web **规则** 页可视化保存。

```json
{
  "profit_take": { "cycle": [15, 35], "growth": [25, 50], "event": [10, 25] },
  "stop_loss_pct": -8
}
```

## 日常流程

```
盘中：手机 Pages → 速记 Issue
收盘：Actions 自动更新收盘价
      本地 run.bat 更新趋势/逻辑/规则
      生成复盘 → build-pages.bat → git push
      纪律触发 → 飞书推送 → 本地确认执行
```

## CLI

```powershell
python -m src.cli decisions
python -m src.cli review --market-info "..."
python scripts/build_pages.py
python scripts/fetch_prices.py
```

## 仓库

https://github.com/gewei2099-web/thesis-trader
