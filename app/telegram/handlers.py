# =========== handlers.py =========

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command

from app.services.monitoring import MonitoringService
from app.services.ticket_service import TicketService


router = Router()


# ===============================
# START
# ===============================
@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "🚀 Fiber Monitor Bot Aktif\n\n"
        "Gunakan /status untuk cek status OLT."
    )


# ===============================
# STATUS (OPTIONAL DEBUG)
# ===============================
@router.message(Command("status"))
async def status_handler(message: Message):
    await message.answer("⚠️ Status command belum terhubung ke OLT real.")


# ===============================
# FALLBACK
# ===============================
@router.message()
async def fallback_handler(message: Message):
    await message.answer("Perintah tidak dikenali.")


# ===============================
# ACK HANDLER (FIXED)
# ===============================
@router.callback_query(F.data.startswith("ack:"))
async def handle_ack(callback: CallbackQuery):

    alarm_id = callback.data.split(":")[1] if callback.data else None
    user_name = callback.from_user.full_name or "Unknown"

    print(f"[ACK DEBUG] received alarm_id: {alarm_id}")

    result = await TicketService.acknowledge_ticket(alarm_id, user_name)

    if result:

        await callback.answer("ACK berhasil ✅")

        if isinstance(callback.message, Message):
            await callback.message.edit_reply_markup(reply_markup=None)

            await callback.message.answer(
                f"🟡 ACKNOWLEDGED\n\nHandled by : {user_name}"
            )

    else:
        await callback.answer(
            "Sudah di-ACK atau tidak ditemukan ❌",
            show_alert=True
        )