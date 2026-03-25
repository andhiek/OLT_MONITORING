# =========== handlers.py =========

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command

from app.services.monitoring import MonitoringService
from app.services.alarm_persistence import acknowledge_alarm
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

    # =========================
    # ACK ALARM
    # =========================
    success = await acknowledge_alarm(
        alarm_id,
        user=user_name
    )

    if success:

        # =========================
        # UPDATE TICKET
        # =========================
        try:
            await TicketService.acknowledge_ticket(alarm_id, user_name)
        except Exception as e:
            print("Ticket ACK error:", e)

        await callback.answer("ACK berhasil ✅")

        if isinstance(callback.message, Message):

            # hapus tombol
            await callback.message.edit_reply_markup(reply_markup=None)

            # kirim notifikasi ACK
            await callback.message.answer(
                f"🟡 ACKNOWLEDGED\n\nHandled by : {user_name}"
            )

    else:
        await callback.answer(
            "Sudah di-ACK atau tidak ditemukan ❌",
            show_alert=True
        )