# Polymarket Tech Tracker

实时追踪Polymarket科技预测事件，包含阈值跨越检测和长期趋势分析。

## 网站
https://harviex.github.io/polymarket-tech-tracker/

## 三榜单系统

### 1. 1-Hour Watch (实时追踪)
- **功能**：每小时检测阈值跨越（70%/80%/90%）
- **数据**：`docs/data/daily_watch/YYYY-MM-DD.json`
- **脚本**：`detect_crossings.py`
- **触发**：c1的cron任务 `Polymarket-Hourly-Detection`（每小时，除12点）
- **逻辑**：比较当前概率与上一小时快照，记录跨越事件

### 2. Daily Watch (今日跨越)
- **功能**：显示当天所有阈值跨越事件
- **数据**：`docs/data/daily_watch/YYYY-MM-DD.json`
- **重置**：每天12:00由cron任务 `Polymarket-12:00-Reset` 清空
- **时区**：网站使用北京时间（UTC+8）加载数据

### 3. Long-Term Board (长期趋势)
- **功能**：展示70%-99%概率的科技事件（不含100%）
- **数据**：`docs/data/long_term/long_term.json`
- **脚本**：`update_longterm.py`
- **触发**：c1的cron任务 `Polymarket-00:00-LongTerm-Update`（每天00:00）
- **数量**：当前21个事件

## 自动化架构

### c1服务器上的Cron任务（主要）
```bash
# 每天00:00 - 更新Long-Term数据
0 0 * * * cd /home/c1/polymarket-tech-tracker && python3 update_longterm.py

# 每天12:00 - 重置Daily Watch
0 12 * * * cd /home/c1/polymarket-tech-tracker && python3 detect_crossings.py --reset

# 每小时（除12点）- 检测阈值跨越
0 1-11,13-23 * * * cd /home/c1/polymarket-tech-tracker && python3 detect_crossings.py
```

### GitHub Actions（辅助）
- **update.yml**：每小时运行 `fetch_events.py` + `news_fetcher.py`
- **限制**：不包含 `detect_crossings.py` 和 `update_longterm.py`
- **建议**：完整自动化需依赖c1的cron或扩展workflow

## 数据流程

1. **抓取**：从Polymarket Gamma API获取科技事件
   - API: `https://gamma-api.polymarket.com/events?tag_slug=tech&end_date_min=今日&volume_min=10000`
   
2. **处理**：
   - `detect_crossings.py`：检测70%/80%/90%阈值跨越
   - `update_longterm.py`：更新70%-99%事件到Long-Term榜
   
3. **存储**：
   - Daily Watch: `docs/data/daily_watch/YYYY-MM-DD.json`
   - Long-Term: `docs/data/long_term/long_term.json`
   - 快照: `docs/data/previous_snapshot.json`（每天首次运行自动清理旧快照）

4. **展示**：
   - 前端: `docs/index.html` + `docs/js/app.js`
   - 时区处理: 北京时间（UTC+8）

## 关键文件

| 文件 | 用途 |
|------|------|
| `detect_crossings.py` | 阈值跨越检测（70%/80%/90%） |
| `update_longterm.py` | Long-Term数据更新（70%-99%事件） |
| `fetch_events.py` | 基础事件数据抓取（GitHub Actions用） |
| `news_fetcher.py` | 新闻抓取（可选） |
| `docs/js/app.js` | 前端逻辑（时区处理、数据渲染） |
| `docs/index.html` | 网站主页面 |

## 用户偏好

- ❌ **不记录100%事件**（已过滤）
- ✅ **只保留70%-99%概率事件**
- ✅ **快照自动清理**：每天首次运行删除前一天数据
- ✅ **时区修复**：网站使用北京时间（UTC+8）

## 最近更新

- **2026-05-05**：时区修复（app.js），快照自动清理，清理100%事件
- **Commit**: `0720d21`

## 技术栈

- 后端: Python 3.11+
- 前端: Vanilla JavaScript + HTML/CSS
- 数据: JSON文件存储
- 部署: GitHub Pages
- 自动化: Cron (c1) + GitHub Actions

## 注意事项

⚠️ **GitHub Actions不完整**：仅运行基础数据抓取，阈值检测和Long-Term更新需依赖c1服务器。
