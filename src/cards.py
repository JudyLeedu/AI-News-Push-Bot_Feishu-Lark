"""飞书卡片消息构建模块

卡片设计规范（PRD v53）：
- 日报 ☕ blue：Daily Insight 前置，💡斜体层级差，不显示来源，最多2条分隔线
- 周报 🍺 turquoise：来源日期单行括号，摘要+观点成组，引用+Insight成组，最多2条分隔线
- 月报 🥤 carmine：多源综合趋势串联，6板块结构，最多2条分隔线
"""
import json
from datetime import datetime


def _card_header(title: str, color: str) -> dict:
    return {
        "title": {"tag": "plain_text", "content": title},
        "template": color,
    }


def _markdown(text: str) -> dict:
    return {"tag": "markdown", "content": text}


def _divider() -> dict:
    return {"tag": "hr"}


# ============================================================
# 日报卡片：☕ Daily Expresso
# ============================================================
def build_daily_card(data: dict) -> str:
    """构建日报飞书卡片，返回 JSON 字符串

    结构：
    ① Daily Insight（前置，今日导读）
    ② <hr>
    ③ 今日 AI 新闻精选（3~5条，💡斜体层级差，不显示来源）
    ④ <hr>
    ⑤ AI Tool 推荐
    """
    today = datetime.now()
    date_str = today.strftime("%Y年%-m月%-d日")
    weekday_map = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday = weekday_map[today.weekday()]
    elements = []

    # ① Daily Insight（前置）
    insight = data.get("insight", "")
    if insight:
        elements.append(_markdown(f"**💬 Daily Insight**\n{insight}"))

    # ② 分隔线
    elements.append(_divider())

    # ③ 今日 AI 新闻精选（3~5条）
    news = data.get("news", [])
    for i, n in enumerate(news[:5], 1):
        title = n.get("title", "")
        summary = n.get("summary", "")
        why = n.get("why", "")
        url = n.get("url", "")
        elements.append(_markdown(
            f"**{i}. [{title}]({url})**\n"
            f"{summary}\n"
            f"*💡 {why}*"
        ))

    # ④ 分隔线
    elements.append(_divider())

    # ⑤ AI Tool
    tool = data.get("tool", {})
    if tool and tool.get("name"):
        tool_name = tool.get("name", "")
        tool_url = tool.get("url", "")
        tool_what = tool.get("what", "")
        tool_problem = tool.get("problem", "")
        elements.append(_markdown(
            f"**🛠️ AI Tool：[{tool_name}]({tool_url})**\n"
            f"{tool_what}\n"
            f"🔧 {tool_problem}"
        ))

    card = {
        "config": {"wide_screen_mode": True},
        "header": _card_header(f"☕ Daily Expresso | {date_str} {weekday}", "blue"),
        "elements": elements,
    }
    return json.dumps(card, ensure_ascii=False)


# ============================================================
# 周报卡片：🍺 Weekly Brew
# ============================================================
def build_weekly_card(data: dict) -> str:
    """构建周报飞书卡片，返回 JSON 字符串

    结构：
    ① 本周长文（标题+来源日期同行括号）
    ② <hr>
    ③ 重要摘要 + 观点（合并成组，空行分隔）
    ④ <hr>
    ⑤ 原英文引用 + Weekly Insight（合并收束）
    """
    today = datetime.now()
    date_str = today.strftime("%Y年%-m月%-d日")
    weekday_map = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday = weekday_map[today.weekday()]
    elements = []

    article = data.get("article", {})

    # ① 本周长文
    if article:
        title = article.get("title", "")
        author = article.get("author", "")
        date = article.get("date", "")
        url = article.get("url", "")
        reason = article.get("reason", "")
        elements.append(_markdown(
            f"**📖 [{title}]({url})**（source: {author}, {date}）\n"
            f"📌 {reason}"
        ))

    # ② 分隔线
    elements.append(_divider())

    # ③ 重要摘要 + 观点（合并为一个内容组，用空行区分）
    summary = data.get("summary", [])
    opinion = data.get("opinion", [])

    parts = []
    if summary:
        lines = ["**📋 重要摘要**"]
        for i, s in enumerate(summary, 1):
            lines.append(f"{i}. {s}")
        parts.append("\n".join(lines))

    if opinion:
        lines = ["**🔍 观点**"]
        for i, o in enumerate(opinion, 1):
            lines.append(f"{i}. {o}")
        parts.append("\n".join(lines))

    if parts:
        elements.append(_markdown("\n\n".join(parts)))

    # ④ 分隔线
    elements.append(_divider())

    # ⑤ 原英文引用 + Weekly Insight（合并为收束区域）
    quotes = data.get("quotes", [])
    insight = data.get("insight", "")

    parts2 = []
    if quotes:
        lines = ["**💬 原英文引用**"]
        for q in quotes:
            lines.append(f"> {q}")
        parts2.append("\n".join(lines))

    if insight:
        parts2.append(f"**🧠 Weekly Insight**\n{insight}")

    if parts2:
        elements.append(_markdown("\n\n".join(parts2)))

    card = {
        "config": {"wide_screen_mode": True},
        "header": _card_header(f"🍺 Weekly Brew | {date_str} {weekday}", "turquoise"),
        "elements": elements,
    }
    return json.dumps(card, ensure_ascii=False)


# ============================================================
# 月报卡片：🥤 Monthly Hand-Drip
# ============================================================
def build_monthly_card(data: dict) -> str:
    """构建月报飞书卡片，返回 JSON 字符串

    结构（6板块）：
    ① 本月关键信号（前置，认知路标，反引号标签）
    ② 本月趋势回顾（多源综合 + 横向串联）
    ③ <hr>
    ④ 值得关注的产品 / 公司
    ⑤ 本月必读
    ⑥ <hr>
    ⑦ 认知更新（元认知沉淀）
    ⑧ 下月关注
    """
    today = datetime.now()
    month_str = today.strftime("%Y年%-m月")
    elements = []

    # ① 本月关键信号
    signals = data.get("signals", [])
    if signals:
        tags = " ".join(f"`{s}`" for s in signals)
        elements.append(_markdown(f"**🏷️ 本月关键信号**\n{tags}"))

    # ② 本月趋势回顾
    trends = data.get("trends", [])
    if trends:
        lines = ["**📊 本月趋势回顾**"]
        for i, t in enumerate(trends, 1):
            name = t.get("name", "")
            events = t.get("events", "")
            why = t.get("why", "")
            lines.append(f"{i}. **{name}**：{events} —— {why}")
        elements.append(_markdown("\n".join(lines)))

    # ③ 分隔线
    elements.append(_divider())

    # ④ 值得关注的产品 / 公司
    companies = data.get("companies", [])
    if companies:
        lines = ["**🏢 值得关注的产品 / 公司**"]
        for i, c in enumerate(companies, 1):
            name = c.get("name", "")
            why_track = c.get("why_track", "")
            lines.append(f"{i}. **{name}**：{why_track}")
        elements.append(_markdown("\n".join(lines)))

    # ⑤ 本月必读
    must_read = data.get("must_read", {})
    if must_read and must_read.get("title"):
        title = must_read.get("title", "")
        author = must_read.get("author", "")
        date = must_read.get("date", "")
        url = must_read.get("url", "")
        reason = must_read.get("reason", "")
        elements.append(_markdown(
            f"**📖 本月必读：[{title}]({url})**（source: {author}, {date}）\n"
            f"📌 {reason}"
        ))

    # ⑥ 分隔线
    elements.append(_divider())

    # ⑦ 认知更新
    cognition = data.get("cognition", [])
    if cognition:
        lines = ["**🧠 认知更新**"]
        for i, c in enumerate(cognition, 1):
            lines.append(f"{i}. {c}")
        elements.append(_markdown("\n".join(lines)))

    # ⑧ 下月关注
    next_month = data.get("next_month", [])
    if next_month:
        lines = ["**🔭 下月关注**"]
        for i, n in enumerate(next_month, 1):
            lines.append(f"{i}. {n}")
        elements.append(_markdown("\n".join(lines)))

    card = {
        "config": {"wide_screen_mode": True},
        "header": _card_header(f"🥤 Monthly Hand-Drip | {month_str}", "carmine"),
        "elements": elements,
    }
    return json.dumps(card, ensure_ascii=False)
