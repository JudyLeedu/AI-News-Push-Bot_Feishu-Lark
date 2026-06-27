"""内容加工模块：调用 LLM 生成日报/周报/月报内容"""
import json
from openai import AsyncOpenAI
from src.config import get_config


def _get_client() -> AsyncOpenAI:
    cfg = get_config()["llm"]
    return AsyncOpenAI(
        api_key=cfg["api_key"],
        base_url=cfg["api_base"],
    )


# ============================================================
# 日报加工：Daily Expresso
# ============================================================
DAILY_PROMPT = """你是一个 AI 资讯分频推送机器人，请根据以下今日 AI 资讯列表，生成日报 Daily Expresso 的内容。

## 内容要求

1. **Daily Insight**（前置，作为今日导读）
   - 对当天整体信号的简短判断
   - 放在新闻之前，让读者先建立认知框架再看新闻
   - 控制在 2~3 句话以内
   - **不要**在判断内容前加任何前缀文字（如「今日的主线：」等），直接输出判断内容本身

2. **今日 AI 新闻精选**：从资讯中选出 3~5 条最重要的，每条包含：
   - 标题（中文，蓝色可点击链接）
   - 一句话摘要
   - 为什么值得关注（产品经理视角，用斜体，与摘要形成视觉层级差——摘要回答「是什么」，关注理由回答「所以呢」）
   - 原文链接
   - **不显示来源名称**

3. **AI Tool**：推荐 1 个当天值得关注的 AI 工具/产品，包含：
   - 产品名称（可点击链接）
   - 这个产品是什么
   - 它解决什么问题

## 输出格式

请以 JSON 格式返回：
{
  "insight": "Daily Insight 内容（2~3句话，无前缀）",
  "news": [
    {
      "title": "中文标题",
      "summary": "一句话摘要",
      "why": "为什么值得关注（产品经理视角）",
      "url": "原文链接"
    }
  ],
  "tool": {
    "name": "工具名称",
    "url": "工具官网链接",
    "what": "这个产品是什么",
    "problem": "它解决什么问题"
  }
}

## 风格约束
- 偏快读、信息密度高、适合晨间 3 分钟快速浏览
- 卡片内最多使用 2 条分隔线，其余用空行和 section header 区分

以下是今日资讯：
{items}
"""


async def generate_daily(items: list[dict]) -> dict:
    """生成日报内容"""
    cfg = get_config()["llm"]
    client = _get_client()

    items_text = "\n\n".join(
        f"- 标题：{it['title']}\n  来源：{it['source']}\n  链接：{it['url']}\n  摘要：{it['summary']}"
        for it in items[:15]
    )

    resp = await client.chat.completions.create(
        model=cfg["model"],
        messages=[{"role": "user", "content": DAILY_PROMPT.format(items=items_text)}],
        temperature=cfg.get("temperature", 0.7),
        max_tokens=cfg.get("max_tokens", 4096),
        response_format={"type": "json_object"},
    )

    content = resp.choices[0].message.content
    return json.loads(content)


# ============================================================
# 周报加工：Weekly Brew
# ============================================================
WEEKLY_PROMPT = """你是一个 AI 资讯分频推送机器人，请从以下候选文章中，选择**一篇**最值得产品经理精读的长文，生成周报 Weekly Brew 的内容。

## 内容要求

1. **本周长文**：
   - 原文标题（蓝色可点击链接）+ 来源和日期在同一行括号内
   - 格式：📖 [文章标题]（source: 作者/来源, 发布日期）
   - 选择理由

2. **重要摘要 + 观点**（合并为一个内容组，用空行区分）：
   - 重要摘要：提炼 3~5 个核心观点，使用数字序号（1. 2. 3.）
   - 观点：从产品经理视角判断，使用数字序号（1. 2. 3.）
   - 摘要回答「文章说了什么」，观点回答「这意味着什么」

3. **原英文引用 + Weekly Insight**（合并为收束区域）：
   - 原英文引用：1~3 句英文原句
   - Weekly Insight：一句高层结论

## 输出格式

请以 JSON 格式返回：
{
  "article": {
    "title": "原文标题",
    "author": "作者/来源",
    "date": "发布日期",
    "url": "原文链接",
    "reason": "选择理由"
  },
  "summary": ["核心观点1", "核心观点2", "核心观点3"],
  "opinion": ["判断1", "判断2", "判断3"],
  "quotes": ["英文引用1", "英文引用2"],
  "insight": "Weekly Insight 收束结论"
}

## 风格约束
- 核心不是「信息罗列」，而是「深度解读一篇文章」
- 体现 PM 视角，不是媒体转述风格
- 卡片内最多使用 2 条分隔线
- 摘要和观点使用数字序号，不使用圆点

以下是候选文章：
{items}
"""


async def generate_weekly(items: list[dict]) -> dict:
    """生成周报内容"""
    cfg = get_config()["llm"]
    client = _get_client()

    items_text = "\n\n".join(
        f"- 标题：{it['title']}\n  来源：{it['source']}\n  链接：{it['url']}\n  摘要：{it['summary']}"
        for it in items[:10]
    )

    resp = await client.chat.completions.create(
        model=cfg["model"],
        messages=[{"role": "user", "content": WEEKLY_PROMPT.format(items=items_text)}],
        temperature=cfg.get("temperature", 0.7),
        max_tokens=cfg.get("max_tokens", 4096),
        response_format={"type": "json_object"},
    )

    content = resp.choices[0].message.content
    return json.loads(content)


# ============================================================
# 月报加工：Monthly Hand-Drip
# ============================================================
MONTHLY_PROMPT = """你是一个 AI 资讯分频推送机器人，请根据以下本月 AI 资讯列表，生成月报 Monthly Hand-Drip 的内容。

月报的本质是「把一个月零散信息压缩成认知」——从多个信源综合提炼本月 AI 趋势主线，不是单篇深度解读。与周报的核心区别：周报是「这篇文章说了什么」，月报是「这个月 AI 世界发生了什么值得我更新认知的事」。

## 内容要求

1. **本月关键信号**（前置，作为认知路标）
   - 2~3 个关键词或短语
   - 用行内代码样式（反引号包裹），视觉上成为标签

2. **本月趋势回顾**（月报灵魂——多源综合 + 横向串联）
   - 3~5 条本月最重要的 AI 趋势
   - 每条包含：趋势名称（加粗）、代表事件或数据点、为什么重要（产品经理视角）
   - 综合多个信源的信息串成主线，不是孤立罗列

3. **值得关注的产品 / 公司**
   - 2~3 个值得产品经理关注的动态
   - 简要说明为什么值得跟踪

4. **本月必读**
   - 推荐 1 篇最值得深度阅读的文章
   - 格式：📖 [文章标题]（source: 作者/来源, 发布日期）
   - 说明为什么这篇代表本月最重要的信号

5. **认知更新**（月报区别于周报的核心板块）
   - 这个月改变了什么看法 / 确认了什么判断 / 新增了什么关注点
   - 元认知层面的沉淀，不是复述文章内容

6. **下月关注**
   - 1~2 个下个月应该盯的方向或事件

## 输出格式

请以 JSON 格式返回：
{
  "signals": ["关键词1", "关键词2", "关键词3"],
  "trends": [
    {
      "name": "趋势名称",
      "events": "代表事件或数据点",
      "why": "为什么重要（产品经理视角）"
    }
  ],
  "companies": [
    {
      "name": "产品/公司名称",
      "why_track": "为什么值得跟踪"
    }
  ],
  "must_read": {
    "title": "文章标题",
    "author": "作者/来源",
    "date": "发布日期",
    "url": "原文链接",
    "reason": "为什么这篇代表本月最重要的信号"
  },
  "cognition": ["认知更新1", "认知更新2"],
  "next_month": ["下月关注1", "下月关注2"]
}

## 风格约束
- 比周报更强调趋势提炼与长期影响
- 月报与周报的结构有明显差异：月报有「本月关键信号」标签、认知更新板块、下月关注板块
- 卡片内最多使用 2 条分隔线

以下是本月资讯：
{items}
"""


async def generate_monthly(items: list[dict]) -> dict:
    """生成月报内容"""
    cfg = get_config()["llm"]
    client = _get_client()

    items_text = "\n\n".join(
        f"- 标题：{it['title']}\n  来源：{it['source']}\n  链接：{it['url']}\n  摘要：{it['summary']}"
        for it in items[:10]
    )

    resp = await client.chat.completions.create(
        model=cfg["model"],
        messages=[{"role": "user", "content": MONTHLY_PROMPT.format(items=items_text)}],
        temperature=cfg.get("temperature", 0.7),
        max_tokens=cfg.get("max_tokens", 4096),
        response_format={"type": "json_object"},
    )

    content = resp.choices[0].message.content
    return json.loads(content)
