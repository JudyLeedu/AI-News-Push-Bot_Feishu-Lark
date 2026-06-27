"""定时调度模块 + 主入口

支持两种运行模式：
1. GitHub Actions：通过 workflow dispatch / cron 触发，执行单次推送后退出
2. 自托管：APScheduler 常驻进程，按 cron 表达式定时触发
"""
import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config import load_config, get_config
from src.collector import collect_content
from src.processor import generate_daily, generate_weekly, generate_monthly
from src.cards import build_daily_card, build_weekly_card, build_monthly_card
from src.feishu import FeishuClient

# ---------- 日志 ----------
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

feishu = FeishuClient()


# ---------- 获取接收人 ----------
async def get_recipients() -> list[str]:
    """获取所有推送目标用户的 open_id"""
    cfg = get_config()["feishu"]
    recipients = cfg.get("recipients", [])
    open_ids = []
    for r in recipients:
        email = r.get("email", "")
        if email:
            oid = await feishu.get_user_by_email(email)
            if oid:
                open_ids.append(oid)
                logger.info(f"用户 {email} -> open_id={oid}")
            else:
                logger.warning(f"无法查询用户 {email} 的 open_id")
    return open_ids


# ---------- 推送任务 ----------
async def push_daily():
    """日报推送"""
    logger.info("========== 日报任务开始 ==========")
    try:
        items = await collect_content("daily")
        if not items:
            logger.warning("日报：未采集到内容")
            return

        logger.info(f"日报：采集到 {len(items)} 条内容")
        data = await generate_daily(items)
        card = build_daily_card(data)

        open_ids = await get_recipients()
        for oid in open_ids:
            ok = await feishu.send_card(oid, card)
            logger.info(f"日报推送 -> {oid}: {'成功' if ok else '失败'}")
    except Exception as e:
        logger.exception(f"日报任务异常: {e}")
    logger.info("========== 日报任务结束 ==========")


async def push_weekly():
    """周报推送"""
    logger.info("========== 周报任务开始 ==========")
    try:
        items = await collect_content("weekly")
        if not items:
            logger.warning("周报：未采集到内容")
            return

        logger.info(f"周报：采集到 {len(items)} 条内容")
        data = await generate_weekly(items)
        card = build_weekly_card(data)

        open_ids = await get_recipients()
        for oid in open_ids:
            ok = await feishu.send_card(oid, card)
            logger.info(f"周报推送 -> {oid}: {'成功' if ok else '失败'}")
    except Exception as e:
        logger.exception(f"周报任务异常: {e}")
    logger.info("========== 周报任务结束 ==========")


async def push_monthly():
    """月报推送（含月末判断）"""
    # 检查是否为当月最后一天
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    if today.month == tomorrow.month:
        logger.info(f"月报：今天 ({today.strftime('%Y-%m-%d')}) 不是本月最后一天，跳过")
        return

    logger.info("========== 月报任务开始 ==========")
    try:
        items = await collect_content("monthly")
        if not items:
            logger.warning("月报：未采集到内容")
            return

        logger.info(f"月报：采集到 {len(items)} 条内容")
        data = await generate_monthly(items)
        card = build_monthly_card(data)

        open_ids = await get_recipients()
        for oid in open_ids:
            ok = await feishu.send_card(oid, card)
            logger.info(f"月报推送 -> {oid}: {'成功' if ok else '失败'}")
    except Exception as e:
        logger.exception(f"月报任务异常: {e}")
    logger.info("========== 月报任务结束 ==========")


# ---------- 手动触发 ----------
async def trigger_manual(frequency: str):
    """手动触发推送（用于测试 / GitHub Actions）"""
    if frequency == "daily":
        await push_daily()
    elif frequency == "weekly":
        await push_weekly()
    elif frequency == "monthly":
        await push_monthly()
    else:
        logger.error(f"未知频次: {frequency}")


# ---------- 启动调度器（自托管模式）----------
def start_scheduler():
    """启动 APScheduler 定时任务"""
    cfg = get_config()["schedule"]
    tz = cfg.get("timezone", "Asia/Shanghai")

    scheduler = AsyncIOScheduler(timezone=tz)

    # 日报：每天 08:30
    daily = cfg["daily"]
    scheduler.add_job(
        push_daily,
        CronTrigger(hour=daily["hour"], minute=daily["minute"], timezone=tz),
        id="push_daily",
        name="日报推送",
        replace_existing=True,
    )
    logger.info(f"日报任务已注册：每天 {daily['hour']:02d}:{daily['minute']:02d}")

    # 周报：每周六 08:30
    weekly = cfg["weekly"]
    scheduler.add_job(
        push_weekly,
        CronTrigger(
            day_of_week=weekly["day_of_week"],
            hour=weekly["hour"],
            minute=weekly["minute"],
            timezone=tz,
        ),
        id="push_weekly",
        name="周报推送",
        replace_existing=True,
    )
    logger.info(f"周报任务已注册：每周{weekly['day_of_week']} {weekly['hour']:02d}:{weekly['minute']:02d}")

    # 月报：每月最后一天 08:30
    monthly = cfg["monthly"]
    scheduler.add_job(
        push_monthly,
        CronTrigger(
            day=monthly["day"],
            hour=monthly["hour"],
            minute=monthly["minute"],
            timezone=tz,
        ),
        id="push_monthly",
        name="月报推送",
        replace_existing=True,
    )
    logger.info(f"月报任务已注册：每月最后一天 {monthly['hour']:02d}:{monthly['minute']:02d}")

    scheduler.start()
    logger.info("调度器已启动")
    return scheduler


# ---------- 主入口 ----------
async def main():
    load_config()

    # 检查命令行参数
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "test":
            freq = sys.argv[2] if len(sys.argv) > 2 else "daily"
            logger.info(f"手动触发 {freq} 推送...")
            await trigger_manual(freq)
            return
        elif cmd == "scheduler":
            pass  # 继续启动调度器
        else:
            logger.error(f"未知命令: {cmd}")
            return

    # 启动调度器（自托管模式）
    scheduler = start_scheduler()

    logger.info("AI 资讯分频推送机器人已启动，等待定时触发...")
    logger.info("按 Ctrl+C 停止")

    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logger.info("正在关闭...")
        scheduler.shutdown(wait=False)
        logger.info("已停止")


if __name__ == "__main__":
    asyncio.run(main())
