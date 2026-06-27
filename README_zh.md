# 飞书 AI 资讯分频推送机器人

[English](README.md) | [中文](README_zh.md)

一个智能、零维护的飞书 AI 资讯策展人。它会自动抓取 20+ 顶级信息源，使用大模型（LLM）过滤噪音，并按三种频率将深度洞察推送到你的飞书私聊：Daily Expresso（每日快报）、Weekly Brew（每周深度）和 Monthly Hand-Drip（每月宏观趋势）。通过 GitHub Actions 实现全自动化。

## 卡片设计

| 发送频率 | 名称 | 标题颜色 | 内容风格 |
|-----------|------|-------------|---------------|
| 每日 | ☕ Daily Expresso | 蓝色 (Blue) | 快速浏览，晨间 3 分钟速读 |
| 每周 | 🍺 Weekly Brew | 绿松石 (Turquoise) | 深度聚焦单篇长文剖析 |
| 每月 | 🥤 Monthly Hand-Drip | 胭脂红 (Carmine) | 多源综合趋势与宏观信号提炼 |

## 核心功能

- **3 种频次分层**，具有独立的卡片设计和内容策略
- **日报 (Daily)**：3-5 条 AI 核心新闻 + 每日洞察 + 1 个 AI 工具推荐
- **周报 (Weekly)**：精选本周最值得阅读的一篇长文，提炼核心摘要、观点与金句
- **月报 (Monthly)**：多源综合趋势提炼，包含 6 大板块（关键信号、趋势、公司、必读、认知更新、下月关注）
- **多源数据采集**：支持通过 RSS 和网页爬虫抓取精选信源
- **大模型内容处理**：调用兼容 OpenAI 的 API 进行摘要总结和洞察生成
- **飞书交互式卡片**：色彩丰富的卡片消息，支持 Markdown 原生排版

## 准备工作

- Python 3.12+
- 一个拥有机器人能力的[飞书开放平台](https://open.feishu.cn/)自建应用
- 一个兼容 OpenAI 格式的 API Key（推荐使用 GPT-4o 或同级别模型）

## 快速开始

### 1. 克隆与配置

```bash
git clone https://github.com/YOUR_USERNAME/ai-news-bot.git
cd ai-news-bot
cp config.example.yaml config.yaml
```

编辑 `config.yaml` 填入你的密钥：

```yaml
feishu:
  app_id: "cli_xxxxxxxxxxxxx"
  app_secret: "your_app_secret_here"
  recipients:
    - email: "your_email@example.com"

llm:
  api_base: "https://api.openai.com/v1"
  api_key: "sk-your-api-key-here"
  model: "gpt-4o"
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 测试推送

```bash
# 测试日报推送
python -m src.main test daily

# 测试周报推送
python -m src.main test weekly

# 测试月报推送
python -m src.main test monthly
```

### 4. 启动调度器 (自建服务器部署)

```bash
python -m src.main scheduler
```

或者使用启动脚本（会自动创建虚拟环境）：

```bash
bash start.sh
```

## GitHub Actions (开源最推荐方式，完全免费)

本项目内置了 GitHub Actions 工作流，无需服务器即可免费实现云端定时推送：

1. Fork 本仓库
2. 进入仓库的 **Settings > Secrets and variables > Actions**
3. 添加以下 Secrets 变量：

| Secret | 描述 |
|--------|-------------|
| `FEISHU_APP_ID` | 你的飞书应用 App ID |
| `FEISHU_APP_SECRET` | 你的飞书应用 App Secret |
| `FEISHU_RECIPIENT_EMAIL` | 接收推送的飞书邮箱 |
| `LLM_API_KEY` | 兼容 OpenAI 格式的 API Key |
| `LLM_API_BASE` | API 基础地址 (默认: `https://api.openai.com/v1`) |
| `LLM_MODEL` | 模型名称 (默认: `gpt-4o`) |

4. 在 **Actions** 标签页中启用对应的工作流

工作流默认执行时间：
- **日报 (Daily)**: 每天北京时间 08:30
- **周报 (Weekly)**: 每周六北京时间 08:30
- **月报 (Monthly)**: 每月最后一天北京时间 08:30

你也可以通过 `workflow_dispatch` 手动触发任意工作流。

## Docker (自建服务器部署)

```bash
docker build -t ai-news-bot .
docker run -d --name ai-news-bot -v $(pwd)/config.yaml:/app/config.yaml ai-news-bot
```

## 项目结构

```
ai-news-bot/
├── .github/workflows/
│   ├── daily.yml          # GitHub Actions: 日报推送
│   ├── weekly.yml         # GitHub Actions: 周报推送
│   └── monthly.yml        # GitHub Actions: 月报推送
├── src/
│   ├── config.py          # 配置加载器 (YAML + 环境变量)
│   ├── collector.py       # RSS + Web 内容采集器
│   ├── processor.py       # 大模型 Prompt 与内容生成
│   ├── cards.py           # 飞书卡片构建器
│   ├── feishu.py          # 飞书 API 客户端
│   └── main.py            # 调度器与程序入口
├── config.example.yaml    # 配置文件模板
├── requirements.txt       # Python 依赖
├── Dockerfile             # Docker 镜像构建
├── start.sh               # 快速启动脚本
└── .gitignore
```

## 默认信息源 (News Sources)

### 日报 (Daily)
- Hacker News, TLDR AI, The Rundown AI, Product Hunt
- OpenAI News, Lenny's Newsletter, Latent Space, YC Combinator, TechCrunch AI

### 周报 (Weekly)
- Simon Willison, The Rundown AI, Anthropic Blog, HuggingFace Daily Papers
- Latent Space, Google DeepMind Blog, Meta AI Blog

### 月报 (Monthly)
- a16z AI, Stanford HAI, State of AI, Sequoia AI, McKinsey AI Insights

## 许可证

MIT
