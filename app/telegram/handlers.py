## =========== handlers.py =========


from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command

from app.services.monitoring import MonitoringService
from app.services.alarm_persistence import acknowledge_alarm


router = Router()

@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "🚀 Fiber Monitor Bot Aktif\n\n"
        "Gunakan /status untuk cek status OLT."
    )




@router.message(Command("status"))
async def status_handler(message: Message):
    data: dict[str, str] = await MonitoringService(olt="default").get_status()

    text = (
        "📡 OLT STATUS\n\n"
        f"Status : {data['olt_status']}\n"
        f"ONU Active : {data['active_onu']}\n"
        f"ONU Down : {data['down_onu']}"
    )

    await message.answer(text)

'''@router.message()
async def debug_id(message: Message):
    print("CHAT ID:", message.chat.id)
    await message.reply(f"Your chat id: {message.chat.id}")
'''

'''@router.message()
async def get_id(message: Message):
    await message.reply(f"Your ID: {message.chat.id}")
'''
@router.message()
async def fallback_handler(message: Message):
    await message.answer("Perintah tidak dikenali.")
    
@router.callback_query(F.data.startswith("ack:"))
async def handle_ack(callback: CallbackQuery):
    alarm_id = callback.data.split(":")[1] if callback.data else None

    success = await acknowledge_alarm(alarm_id,user = callback.from_user)

    if success:
        await callback.answer("Alarm acknowledged ✅")

        # Hapus tombol jika message bisa diedit
        if isinstance(callback.message, Message):
            await callback.message.edit_reply_markup(reply_markup=None)
            await callback.message.answer("👤 Alarm sudah di-ACK oleh operator.")
        
    else:
        await callback.answer("Alarm sudah di-ack atau tidak ditemukan ❌")