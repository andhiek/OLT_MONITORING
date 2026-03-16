## ============ bot.py ==============


import asyncio
from aiogram import Bot, Dispatcher

from app.core.config import BOT_TOKEN
from app.telegram.handlers import router
from app.core.scheduler import monitoring_loop


async def start_bot():
    await _run()


async def run_monitoring(bot: Bot):

    while True:

        try:
            await monitoring_loop(bot)

        except Exception as e:
            print("❌ Monitoring loop error:", e)

        await asyncio.sleep(5)


async def _run():

    if BOT_TOKEN is None:
        raise ValueError("BOT_TOKEN is not set")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(router)

    # monitoring background task
    asyncio.create_task(run_monitoring(bot))

    print("🚀 Fiber Monitor Started")
    print("🤖 Telegram Bot Running...")

    await dp.start_polling(bot)