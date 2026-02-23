## ============ bot.py ==============


import asyncio
from aiogram import Bot, Dispatcher
from app.core.config import BOT_TOKEN
from app.telegram.handlers import router
from app.core.scheduler import monitoring_loop

def start_bot():
    asyncio.run(_run())
    
    

async def _run():
    if BOT_TOKEN is None:
        raise ValueError("BOT_TOKEN is not set")
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(router)
    
    # Jalankan monitoring loop background
    asyncio.create_task(monitoring_loop(bot))

    print("🤖 Telegram Bot Running...")
    await dp.start_polling(bot)


