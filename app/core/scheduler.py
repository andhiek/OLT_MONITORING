# =========== scheduler.py ============

import asyncio
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.services.monitoring import MonitoringService
from app.services.alarm import AlarmService
from app.services.olt_service import get_active_olts
from app.services.onu_service import save_onu_data
from app.services.alarm_persistence import create_alarm, resolve_alarm
from app.services.topology_service import load_topology, detect_fiber_cut
from app.services.topology_service import detect_root_cause


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
                elif alert["event"] == "ONU_ONLINE":

                    onu_uuid = onu_mapping.get(alert.get("onu_index"))

                    resolved = await resolve_alarm(
                        olt,
                        onu_uuid,
                        "ONU_OFFLINE"
                    )

                    if resolved:
                        text += f"\nDuration: {resolved['duration']}"

                        if resolved["acknowledged_by"]:
                            text += f"\nHandled by: {resolved['acknowledged_by']}"

                        await bot.send_message(
                            olt.client.telegram_chat_id,
                            text
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
                    print("Sending alarm for ONU", alarm_id)

            except Exception as e:
                print(f"Telegram error ({olt.name}): {e}")
 
# ===============================
# Main Monitoring Loop
# ===============================
async def monitoring_loop(bot):

    while True:

        print("---- MONITORING CYCLE ----", datetime.now())

        olts = await get_active_olts()

        if not olts:
            print("No active OLT configured")
            await asyncio.sleep(30)
            continue

        tasks = [
            process_olt(bot, olt)
            for olt in olts
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for r in results:
            if isinstance(r, Exception):
                print("Monitoring task error:", r)
                
        fiber_alarms = await detect_fiber_cut()

        for alarm in fiber_alarms:
            print("FIBER CUT DETECTED:", alarm)

                
        # ===============================
        # ROOT CAUSE DETECTION
        # ===============================

        events = await detect_root_cause()

        for event in events:

            if event["type"] == "fiber_cut":

                text = (
                    "🚨 *FIBER CUT SUSPECTED*\n\n"
                    f"OLT : `{event['olt']}`\n"
                    f"PON : `{event['pon']}`\n"
                    f"Splitter : `{event['splitter']}`\n\n"
                    f"ONU Down : {event['down']} / {event['total']}"
                )

                # kirim ke client yang punya OLT ini
                for olt in olts:

                    if olt.name == event["olt"] and olt.client.telegram_chat_id:

                        try:

                            await bot.send_message(
                                chat_id=olt.client.telegram_chat_id,
                                text=text,
                                parse_mode="Markdown"
                            )

                        except Exception as e:

                            print("Telegram FiberCut error:", e)
                            
                            
        await asyncio.sleep(30) # delay 30 detik sebelum next cycle