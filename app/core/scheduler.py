# =========== scheduler.py ============

import asyncio
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.services.monitoring import MonitoringService
from app.services.alarm import AlarmService
from app.services.olt_service import get_active_olts
from app.services.onu_service import save_onu_data
from app.services.alarm_persistence import create_alarm, resolve_alarm


# ===============================
# Telegram Formatter
# ===============================
def format_telegram_message(olt_name, alert):
    now = datetime.now().strftime("%H:%M")

    event = alert.get("event")
    onu = alert.get("onu_index")
    message = alert.get("message")

    if event == "ONU_OFFLINE":
        icon = "🔴"
        body = f"ONU: {onu}\nStatus: OFFLINE"

    elif event == "ONU_ONLINE":
        icon = "🟢"
        body = f"ONU: {onu}\nStatus: BACK ONLINE"

    elif event == "ONU_LOW_POWER":
        icon = "🟡"
        body = f"ONU: {onu}\nStatus: REDAMAN TINGGI"

    elif event == "ONU_POWER_NORMAL":
        icon = "🟢"
        body = f"ONU: {onu}\nStatus: POWER NORMAL"

    else:
        icon = "⚪"
        body = message

    return f"{icon} [{olt_name}]\n{body}\nTime: {now}"


# ===============================
# Process Single OLT
# ===============================
async def process_olt(bot, olt):
    service = MonitoringService(olt)

    try:
        data = await service.get_status()
        onu_mapping = await save_onu_data(olt, data.get("onu_list", []))

        if "error" in data:
            alerts = [{
                "event": "SNMP_ERROR",
                "message": data["error"]
            }]
        else:
            alerts = AlarmService.evaluate(olt.id, data)

            

    except Exception as e:
        if olt.client.telegram_chat_id:
            # jika error monitoring, kirin notif ke telegram
            try:
                await bot.send_message(
                    olt.client.telegram_chat_id,
                    f"[{olt.name}] ❌ Monitoring Error: {e}"
                )
            except Exception:
                pass
        return

    # Telegram Notification
    if alerts and olt.client.telegram_chat_id:
        for alert in alerts:
            try:
                text = format_telegram_message(olt.name, alert)
                keyboard = None
                alarm_id = None  # <- penting!

                # Hanya OFFLINE yang buat alarm + tombol
                if alert["event"] == "ONU_OFFLINE":
                    onu_uuid = onu_mapping.get(alert.get("onu_index"))

                    alarm_id = await create_alarm(
                        olt,
                        onu_uuid,
                        "ONU_OFFLINE",
                        alert["message"]
                    )

                if alarm_id:
                    keyboard = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="✅ ACK",
                                    callback_data=f"ack:{alarm_id}"
                                )
                            ]
                        ]
                    )

                await bot.send_message(
                    olt.client.telegram_chat_id,
                    text,
                    reply_markup=keyboard
                )

            except Exception as e:
                print(f"Telegram error ({olt.name}): {e}")
# ===============================
# Main Monitoring Loop
# ===============================
async def monitoring_loop(bot):

    while True:
        olts = await get_active_olts()

        tasks = [
            process_olt(bot, olt)
            for olt in olts
        ]

        # Jalankan semua OLT secara parallel
        await asyncio.gather(*tasks, return_exceptions=True)

        await asyncio.sleep(30)