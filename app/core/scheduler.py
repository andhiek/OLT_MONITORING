# =========== scheduler.py ============

import asyncio
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.services.monitoring import MonitoringService
from app.services.olt_service import get_active_olts
from app.services.onu_service import save_onu_data
from app.services.alarm_persistence import create_alarm, resolve_alarm
from app.services.topology_service import detect_root_cause
from app.services.ticket_service import TicketService


# ===============================
# TELEGRAM FORMAT (FINAL NOC STYLE)
# ===============================
def format_telegram(alert, olt_name, ticket_id=None, resolved=None):
    now = datetime.now().strftime("%H:%M")

    event = alert.get("event")
    onu = str(alert.get("device_id"))
    pon = alert.get("pon_port")

    # =============================
    # FIBER CUT
    # =============================
    if event == "FIBER_CUT":
        text = (
            "🚨 FIBER CUT\n\n"
            f"OLT     : {olt_name}\n"
            f"PON     : {pon}\n"
            f"Impact  : {alert.get('count')} ONU DOWN\n\n"
            f"Time    : {now}"
        )
        if ticket_id:
            text += f"\nTicket  : #{ticket_id}"
        return text

    # =============================
    # ONU DOWN
    # =============================
    if event == "ONU_OFFLINE":
        text = (
            "🚨 ONU DOWN\n\n"
            f"OLT     : {olt_name}\n"
            f"ONU     : {onu}\n"
            f"Status  : OFFLINE\n\n"
            f"Time    : {now}"
        )
        if ticket_id:
            text += f"\nTicket  : #{ticket_id}"
        return text

    # =============================
    # RECOVERY
    # =============================
    if event == "ONU_ONLINE":
        text = (
            "✅ RECOVERY\n\n"
            f"OLT     : {olt_name}\n"
            f"ONU     : {onu}\n"
            f"Status  : BACK ONLINE\n"
        )

        if resolved:
            text += f"\nDuration: {resolved['duration']}"
            if resolved.get("acknowledged_by"):
                text += f"\nHandled : {resolved['acknowledged_by']}"

        text += f"\n\nTime    : {now}"
        return text

    # =============================
    # LOW POWER
    # =============================
    if event == "ONU_LOW_POWER":
        return (
            "⚠️ SIGNAL ISSUE\n\n"
            f"OLT     : {olt_name}\n"
            f"ONU     : {onu}\n"
            f"Status  : LOW POWER\n\n"
            f"Time    : {now}"
        )

    return f"{alert.get('message')}\nTime: {now}"


# ===============================
# PROCESS PER OLT
# ===============================
async def process_olt(bot, olt):
    service = MonitoringService(olt)

    try:
        data = await service.get_status()

        onu_mapping = await save_onu_data(
            olt, data.get("onu_list", [])
        )

        alerts = data.get("alerts", [])

    except Exception as e:
        if olt.client.telegram_chat_id:
            try:
                await bot.send_message(
                    olt.client.telegram_chat_id,
                    f"[{olt.name}] ❌ Monitoring Error: {e}"
                )
            except Exception:
                pass
        return

    if not alerts or not olt.client.telegram_chat_id:
        return

    # ===============================
    # 🔥 DEDUP ALERT (ANTI SPAM)
    # ===============================
    seen = set()
    unique_alerts = []

    for alert in alerts:
        key = f"{alert.get('device_id')}-{alert.get('event')}-{alert.get('status')}"
        if key in seen:
            continue
        seen.add(key)
        unique_alerts.append(alert)

    alerts = unique_alerts

    # ===============================
    # PROCESS ALERT
    # ===============================
    for alert in alerts:

        alert["olt_id"] = str(alert.get("olt_id")) if alert.get("olt_id") else None
        alert["device_id"] = str(alert.get("device_id")) if alert.get("device_id") else None

        print("🧪 DEBUG ALERT:", alert)

        try:
            if not alert.get("is_root"):
                continue

            device_id = alert.get("device_id")
            device_type = alert.get("device_type")

            onu_uuid = None
            alarm_id = None
            ticket_id = None
            resolved = None

            # =========================
            # DOWN → CREATE
            # =========================
            if alert.get("status") == "DOWN":

                if device_type != "ONU":
                    continue

                onu_uuid = onu_mapping.get(str(device_id))
                if not onu_uuid:
                    continue

                print(f"🎯 Creating ticket for ONU {device_id}")

                result = await TicketService.create_ticket(
                    olt,
                    onu_uuid,
                    alert
                )

                ticket_id = result["ticket_id"]
                alarm_id = result["alarm_id"]

                # 🔥 inject ke alert
                alert["alarm_id"] = alarm_id
                alert["ticket_id"] = str(ticket_id)

                # 🔥 save alarm pakai ID yang sama
                await create_alarm(
                    olt,
                    onu_uuid,
                    alert.get("event"),
                    alert.get("message"),
                    alarm_id=alarm_id
                )

            # =========================
            # UP → RESOLVE
            # =========================
            elif alert.get("status") == "UP":

                if device_type != "ONU":
                    continue

                onu_uuid = onu_mapping.get(str(device_id))
                if not onu_uuid:
                    continue

                resolved = await resolve_alarm(
                    olt,
                    onu_uuid,
                    alert.get("event")
                )

            # =========================
            # FORMAT
            # =========================
            text = format_telegram(
                alert,
                olt.name,
                ticket_id=ticket_id,
                resolved=resolved
            )

            print("Formatted Telegram Text:", text)

            # =========================
            # BUTTON (ONLY FOR DOWN)
            # =========================
            keyboard = None

            if alert.get("status") == "DOWN":
                if not alarm_id:
                    print("❌ SKIP: alarm_id kosong")
                    continue

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

                print(f"Generated keyboard: {alarm_id}")

            await bot.send_message(
                olt.client.telegram_chat_id,
                text,
                reply_markup=keyboard
            )

            print(f"Telegram sent: {alarm_id}")

        except Exception as e:
            print(f"❌ Telegram error ({olt.name}): {e}")


# ===============================
# MAIN LOOP
# ===============================
async def monitoring_loop(bot):

    while True:

        print("---- MONITORING CYCLE ----", datetime.now())

        olts = await get_active_olts()

        if not olts:
            print("No active OLT configured")
            await asyncio.sleep(30)
            continue

        tasks = [process_olt(bot, olt) for olt in olts]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for r in results:
            if isinstance(r, Exception):
                print("Monitoring task error:", r)

        # ===============================
        # ROOT CAUSE (TOPOLOGY)
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

        await asyncio.sleep(30)