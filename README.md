# Polymarket Tech Tracker

实时追踪 Polymarket 预测市场事件，支持 Technology / Culture / Economy 三大分类，包含阈值跨越检测和长期趋势分析。

## 在线访问

**https://harviex.github.io/polymarket-tech-tracker/**

## 功能特性

### 三分类追踪

| 分类 | 标签 | 说明 |
|------|------|------|
| Technology | `tech` | 科技预测市场事件 |
| Culture | `pop-culture` | 流行文化事件 |
| Economy | `business`, `economy` | 商业与经济体事件（合并展示） |

每个分类独立维护数据文件和 cron 任务。

### 双榜单系统

#### 1. Daily Watch（实时追踪）
- **功能**：检测阈值跨越事件（70% / 80% / 90%）
- **数据**：`docs/data/{cat}/daily_watch/YYYY-MM-DD.json`
- **时区**：北京时间（UTC+8）
- **展示**：
  - 同一事件的多次跨越自动归并
  - 显示跨越时间、阈值、概率变化（如 `70.5% → 74.0%`）
  - 历史记录以紫色块展示，倒序排列

#### 2. Long-Term Board（长期趋势）
- **功能**：展示 70%-99% 概率的预测事件（不含 100%）
- **数据**：`docs/data/{cat}/long_term/long_term.json`
- **筛选条件**：TECH 标签、70%-99% 概率、交易量 ≥ 10K、结束时间 ≥ 今日
- **展示**：按次级标签分组，卡片式布局，双列排列
- **特有字段**：`option_text` 显示概率对应的选项文字（如 Yes/No/$1T/75%），绝不重复标题

### 其他功能
- 🔍 实时搜索：同时过滤 Daily Watch 和 Long-Term Board
- 🌐 EN ⇄ 简体中文切换（`docs/locales/`）
- 📱 响应式设计，支持移动端

## 自动化架构

### c1 服务器 Cron 任务

```bash
# 每天 00:00 — 更新 Long-Term 数据（三分类）
0 0 * * * cd /home/c1/polymarket-tech-tracker && python3 update_longterm.py
0 0 * * * cd /home/c1/polymarket-tech-tracker && python3 update_culture.py
0 0 * * * cd /home/c1/polymarket-tech-tracker && python3 update_economy.py

# 每天 12:00 — 重置 Daily Watch
0 12 * * * cd /home/c1/polymarket-tech-tracker && python3 detect_crossings.py --reset

# 每小时（除 12 点）— 检测阈值跨越
0 1-11,13-23 * * * cd /home/c1/polymarket-tech-tracker && python3 detect_crossings.py
```

### GitHub Actions（辅助）
- `update.yml`：每小时运行 `fetch_events.py` + `news_fetcher.py`
- 不包含 `detect_crossings.py` 和 `update_longterm.py`（依赖 c1 cron）

## 数据流程

```
1. 抓取 → Polymarket Gamma API
   API: https://gamma-api.polymarket.com/events?tag_slug={tag}&end_date_min=今日&volume_min=10000

2. 处理
   detect_crossings.py  → 检测阈值跨越（比较当前 vs 上一小时快照）
   update_longterm.py   → 更新 Long-Term 榜（三分类各自独立）
   update_culture.py    → Culture 分类数据更新
   update_economy.py    → Economy 分类数据更新

3. 存储
   Daily Watch: docs/data/{cat}/daily_watch/YYYY-MM-DD.json
   Long-Term:   docs/data/{cat}/long_term/long_term.json
   快照:        docs/data/{cat}/previous_snapshot.json

4. 展示
   docs/index.html + docs/js/app.js（北京时间 UTC+8）
```

## 关键文件

| 文件 | 用途 |
|------|------|
| `detect_crossings.py` | 阈值跨越检测（70%/80%/90%） |
| `update_longterm.py` | Long-Term 数据更新（Technology 分类） |
| `update_culture.py` | Culture 分类数据更新 |
| `update_economy.py` | Economy 分类数据更新 |
| `fetch_events.py` | 基础事件数据抓取（GitHub Actions 用） |
| `news_fetcher.py` | 新闻数据抓取（可选） |
| `analyze_missing.py` | 缺失数据分析工具 |
| `count_tech_events.py` | 事件计数工具 |
| `migrate_boards.py` | 数据迁移工具 |
| `docs/js/app.js` | 前端逻辑（模块模式，三分类 + 语言切换） |
| `docs/index.html` | 网站主页面 |
| `docs/locales/` | EN/CH 语言包 |

## 用户偏好（硬编码）

- ❌ 不记录 100% 事件
- ✅ 只保留 70%-99% 概率事件
- ✅ 快照自动清理（每天首次运行删除前一天数据）
- ✅ 时区：北京时间（UTC+8）
- ✅ `option_text` 字段绝不重复标题

## 技术栈

- **后端**：Python 3.11+
- **前端**：Vanilla JavaScript + HTML/CSS（模块模式）
- **数据**：JSON 文件存储
- **部署**：GitHub Pages
- **自动化**：Cron (c1) + GitHub Actions

## 更新日志

- **2026-05-22**：新增 Culture/Economy 分类、EN/CH 语言切换、option_text 字段、双列布局、历史记录紫色块
- **2026-05-05**：时区修复（app.js）、快照自动清理、过滤 100% 事件

## 注意事项

⚠️ **GitHub Actions 不完整**：仅运行基础数据抓取，阈值检测和 Long-Term 更新依赖 c1 服务器 cron 任务。
