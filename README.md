# thesis-trader

个人交易决策辅助系统：股票池、持仓、逻辑卡片、决策引擎、每日复盘、纪律监督。

## 本地使用（可编辑）

```powershell
cd D:\Projects\thesis-trader
.\setup.ps1
.\run.bat
```

浏览器：**http://localhost:8765**（手机同 WiFi 访问 `http://<电脑IP>:8765`）

## 手机远程查看（Phase 4 · GitHub Pages）

### 1. 推送到 GitHub

```powershell
cd D:\Projects\thesis-trader
git add .
git commit -m "init thesis-trader"
git remote add origin https://github.com/<你的用户名>/thesis-trader.git
git push -u origin main
```

### 2. 启用 GitHub Pages

仓库 **Settings → Pages → Build and deployment**：

- Source: **Deploy from a branch**
- Branch: **main** / **/docs**

保存后访问：`https://<用户名>.github.io/thesis-trader/`

手机浏览器打开后可「添加到主屏幕」，当作 App 使用（只读）。

### 3. 自动每日复盘

已配置 GitHub Actions：

| 工作流 | 触发 | 作用 |
|--------|------|------|
| `Daily Review` | 周一至周五 21:00（北京）+ 手动 | 生成复盘 → 构建 Pages → 提交 |
| `Build Pages` | push 到 main（data/src 变更） | 重建静态站点 |

**手动触发复盘（可填市场信息）：**

GitHub 仓库 → **Actions** → **Daily Review** → **Run workflow** → 填写 `market_info`

**可选 Secret：** 在 Settings → Secrets 添加 `MARKET_INFO`，定时任务会自动使用。

### 4. 本地工作流

```powershell
# 更新持仓/逻辑后，本地构建 Pages 预览
.\build-pages.bat

# 然后提交 data/ 和 docs/
git add data/ docs/
git commit -m "update positions and pages"
git push
```

## 模块

| 模块 | 本地 | Pages |
|------|------|-------|
| watchlist | 可编辑 | 只读 |
| positions | 可编辑 | 只读 |
| thesis | 可编辑 | 只读 |
| decision engine | 实时 | 构建时快照 |
| daily review | 手动粘贴 | Actions 自动生成 |
| discipline | 可确认 | 只读 |

## CLI

```powershell
python -m src.cli decisions
python -m src.cli review --market-info "今日市场信息..."
python -m src.cli build-pages
```

## 数据

- 源数据：`data/`（JSON，纳入 Git）
- 静态站点：`docs/`（由 `scripts/build_pages.py` 生成，纳入 Git）
