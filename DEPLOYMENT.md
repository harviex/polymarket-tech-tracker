# Tech Predictions Tracker - 部署指南

## ✅ 已完成的工作

### 1. 项目结构
```
polymarket-tech-tracker/
├── index.html              # 主页面（卡片式布局）
├── archive.html            # 归档页面（已完结市场）
├── style.css               # 样式（浅色主题默认，支持暗色）
├── script.js               # 前端逻辑（英/中/日三语）
├── data/
│   ├── markets.json        # 活跃市场数据（已抓取20个）
│   └── archive.json        # 归档数据
├── scripts/
│   ├── fetch_polymarket.py # 抓取Polymarket API
│   └── fetch_twitter_news.py # 抓取Twitter新闻
├── .github/workflows/
│   └── update-data.yml     # 每小时自动更新
├── README.md
└── .nojekyll
```

### 2. 核心功能
- ✅ 卡片式布局（参考OpenRouter仪表板）
- ✅ 浅色/暗色主题切换（默认浅色）
- ✅ 英中日三语切换
- ✅ Polymarket科技类市场抓取（已测试，获取20个市场）
- ✅ 响应式设计
- ✅ GitHub Actions自动更新（每小时）
- ✅ 归档页面

### 3. 当前状态
- **本地路径**: `/home/c1/polymarket-tech-tracker`
- **Git仓库**: 已初始化，已提交
- **市场数据**: 已抓取20个科技相关市场
- **GitHub推送**: ❌ 认证失败（需要手动处理）

## ⚠️ 待解决问题

### 1. GitHub推送失败
**原因**: Fine-grained PAT认证方式可能不对

**解决方案（手动执行）**:
```bash
cd /home/c1/polymarket-tech-tracker

# 方案A: 使用gh CLI（如果可用）
gh auth login
gh repo create harviex/polymarket-tech-tracker --public
git push -u origin main

# 方案B: 在GitHub网页创建仓库后推送
# 1. 访问 https://github.com/new
# 2. 创建名为 polymarket-tech-tracker 的公开仓库
# 3. 然后执行：
git remote set-url origin https://github.com/harviex/polymarket-tech-tracker.git
git push -u origin main
# （会提示输入用户名和密码，密码处填入token）
```

### 2. Twitter API 401错误
**原因**: 提供的token可能格式不对或权限不足

**建议**:
- 检查token是否为Twitter API v2 Bearer Token
- 或者使用替代方案：RSS feed抓取（TechCrunch, The Verge等提供RSS）
- 暂时跳过新闻功能，市场数据仍可正常显示

### 3. GitHub Secrets配置（推送成功后）
需要在GitHub仓库设置中添加以下Secrets：
- `TWITTER_API_TOKEN`: Twitter API Bearer Token
- `OPENAI_API_KEY`: OpenAI API Key（用于翻译）

路径：Settings → Secrets and variables → Actions → New repository secret

## 🚀 快速测试本地版本

```bash
cd /home/c1/polymarket-tech-tracker
python3 -m http.server 8080
# 访问 http://192.168.123.101:8080
```

## 📝 后续优化建议

1. **改进市场过滤**: 当前会混入少量非科技市场（如NBA、世界杯），可以优化关键词
2. **新闻抓取**: 考虑使用RSS feed作为Twitter API的替代
3. **AI预测**: 集成GPT-4对市场进行深度分析（而非简单的方向判断）
4. **更多领域**: 科技类稳定后，扩展到政治、体育等领域

## 🔗 相关链接

- **Polymarket API文档**: https://docs.polymarket.com/
- **OpenRouter仪表板参考**: https://harviex.github.io/openrouter-free-dashboard/
- **项目本地路径**: /home/c1/polymarket-tech-tracker

---

**当前状态**: 项目核心功能已完成，等待GitHub推送和Secrets配置后即可全自动运行。
