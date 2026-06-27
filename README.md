# AI News Multi-Frequency Push Bot

[English](README.md) | [中文](README_zh.md)

A smart, zero-maintenance AI news curator for Feishu. It scrapes 20+ top sources, uses LLMs to filter the noise, and delivers insights to your DM at three cadences: Daily Expresso (quick hits), Weekly Brew (deep dives), and Monthly Hand-Drip (macro trends). Fully automated via GitHub Actions.

## Card Designs

| Frequency | Name | Header Color | Content Style |
|-----------|------|-------------|---------------|
| Daily | ☕ Daily Expresso | Blue | Quick scan, 3-min morning read |
| Weekly | 🍺 Weekly Brew | Turquoise | Deep dive on one article |
| Monthly | 🥤 Monthly Hand-Drip | Carmine | Multi-source trend synthesis |

## Features

- **3 frequency tiers** with distinct card designs and content strategies
- **Daily**: 3-5 AI news highlights + Daily Insight + AI Tool recommendation
- **Weekly**: Deep analysis of one must-read article with summary, opinion, and quotes
- **Monthly**: Multi-source trend synthesis with 6 sections (key signals, trends, companies, must-read, cognition updates, next-month focus)
- **Multi-source collection**: RSS feeds and web scraping from curated sources
- **LLM-powered content processing**: Uses OpenAI-compatible API for summarization and insight generation
- **Feishu interactive cards**: Rich card messages with color-coded headers and markdown formatting

## Prerequisites

- Python 3.12+
- A [Feishu Open Platform](https://open.feishu.cn/) app with bot capability
- An OpenAI-compatible API key (GPT-4o recommended)

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/YOUR_USERNAME/ai-news-bot.git
cd ai-news-bot
cp config.example.yaml config.yaml
```

Edit `config.yaml` with your credentials:

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

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Test a push

```bash
# Test daily push
python -m src.main test daily

# Test weekly push
python -m src.main test weekly

# Test monthly push
python -m src.main test monthly
```

### 4. Run the scheduler (self-hosted)

```bash
python -m src.main scheduler
```

Or use the start script:

```bash
bash start.sh
```

## GitHub Actions (Recommended for Open Source)

This project includes GitHub Actions workflows for free cloud scheduling:

1. Fork this repo
2. Go to **Settings > Secrets and variables > Actions**
3. Add the following secrets:

| Secret | Description |
|--------|-------------|
| `FEISHU_APP_ID` | Your Feishu app ID |
| `FEISHU_APP_SECRET` | Your Feishu app secret |
| `FEISHU_RECIPIENT_EMAIL` | Recipient email address |
| `LLM_API_KEY` | Your OpenAI-compatible API key |
| `LLM_API_BASE` | API base URL (default: `https://api.openai.com/v1`) |
| `LLM_MODEL` | Model name (default: `gpt-4o`) |

4. Enable the workflows in the **Actions** tab

The workflows run on:
- **Daily**: Every day at 08:30 Beijing time (UTC 00:30)
- **Weekly**: Every Saturday at 08:30 Beijing time
- **Monthly**: Last day of each month at 08:30 Beijing time

You can also trigger any workflow manually via `workflow_dispatch`.

## Docker (Self-Hosted)

```bash
docker build -t ai-news-bot .
docker run -d --name ai-news-bot -v $(pwd)/config.yaml:/app/config.yaml ai-news-bot
```

## Project Structure

```
ai-news-bot/
├── .github/workflows/
│   ├── daily.yml          # GitHub Actions: daily push
│   ├── weekly.yml         # GitHub Actions: weekly push
│   └── monthly.yml        # GitHub Actions: monthly push
├── src/
│   ├── config.py          # Config loader (YAML + env vars)
│   ├── collector.py       # RSS + web content collection
│   ├── processor.py       # LLM prompts for content generation
│   ├── cards.py           # Feishu card builders
│   ├── feishu.py          # Feishu API client
│   └── main.py            # Scheduler + entry point
├── config.example.yaml    # Configuration template
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker build
├── start.sh               # Quick start script
└── .gitignore
```

## News Sources

### Daily
- Hacker News, TLDR AI, The Rundown AI, Product Hunt
- OpenAI News, Lenny's Newsletter, Latent Space, YC Combinator, TechCrunch AI

### Weekly
- Simon Willison, The Rundown AI, Anthropic Blog, HuggingFace Daily Papers
- Latent Space, Google DeepMind Blog, Meta AI Blog

### Monthly
- a16z AI, Stanford HAI, State of AI, Sequoia AI, McKinsey AI Insights

## License

MIT
