# =========== scheduler.py ============

import asyncio
import os
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.services.monitoring import MonitoringService
from app.services.olt_service import get_active_olts
from app.services.onu_service import save_onu_data
from app.services.alarm_persistence import create_alarm, resolve_alarm
from app.services.topology_service import detect_root_cause
from app.services.ticket_service import TicketService
from app.services.alarm_correlation_service import AlarmCorrelationService
from app.services.incident_correlation_service import IncidentCorrelationService
from app.services.state_cache import STATE


incident_service = IncidentCorrelationService()

print("🔥 Scheduler running PID:", os.getpid())
# ===============================
# TELEGRAM FORMAT
# ===============================
def format_telegram(alert, olt_name, ticket_id=None, resolved=None):
    now = datetime.now().strftime("%H:%M")

    event = alert.get("event")
    onu = str(alert.get("device_id"))

    if event == "ONU_ONLINE":
        text = (
            "✅ RECOVERY\n\n"
            f"OLT     : {olt_name}\n"
            f"ONU     : {onu}\n"
            f"Status  : BACK ONLINE\n"
        )

        if resolved:
            text += f"\nDuration: {resolved['duration']}"
            text += f"\nHandled : {resolved.get('handled_by', 'SYSTEM')}"

        text += f"\n\nTime    : {now}"
        return text

    return f"{alert.get('message')}\nTime: {now}"


# ===============================
# PROCESS PER OLT
# ===============================
async def process_olt(bot, olt):
    print("PROCESS OLT:", olt.name, id(olt))

    service = MonitoringService(olt)
    print("OLT ID:", olt.id)

    try:
        data = await service.get_status()

        onu_mapping = await save_onu_data(
            olt, data.get("onu_list", [])
        )

        raw_alerts = data.get("alerts", [])

    except Exception as e:
        if olt.client.telegram_chat_id:
            await bot.send_message(
                olt.client.telegram_chat_id,
                f"[{olt.name}] ❌ Monitoring Error: {e}"
            )
        return

    if not raw_alerts or not olt.client.telegram_chat_id:
        return

    # ===============================
    # 🔥 DEDUP
    # ===============================
    seen = set()
    alerts = []

    for a in raw_alerts:
        key = f"{a.get('device_id')}-{a.get('event')}-{a.get('status')}"
        if key in seen:
            continue
        seen.add(key)
        alerts.append(a)

    # ===============================
    # 🔥 ALARM CORRELATION (WAJIB)
    # ===============================
    
    

    # ===============================
    # 🔥 INCIDENT LAYER (FINAL CLEAN)
    # ===============================
    incidents = incident_service.process(alerts)

    if "incidents" not in STATE:
        STATE["incidents"] = []

    # hapus incident lama dari OLT ini
    STATE["incidents"] = [
        inc for inc in STATE["incidents"]
        if inc.get("olt_id") != str(olt.id)
    ]

    # inject metadata + simpan
    for inc in incidents:
        inc["olt_id"] = str(olt.id)
        inc["olt_name"] = olt.name

    STATE["incidents"].extend(incidents)

    # ===============================
    # 🚨 INCIDENT LOOP
    # ===============================
    for incident in incidents:
        try:

            root = incident.get("root_alert")
            if not root:
                continue

            if not incident.get("is_new") or incident.get("is_active") is False:
                continue

            if root.get("status") != "DOWN":
                continue

            if root.get("device_type") != "ONU":
                continue

            device_id = str(root.get("device_id"))
            onu_uuid = onu_mapping.get(device_id)

            if not onu_uuid:
                continue

            print(f"🔥 INCIDENT NEW: OLT={olt.name} ROOT={device_id} impact={incident['impact_count']}")
            
            

            # =========================
            # CREATE TICKET
            # =========================
            result = await TicketService.create_ticket(
                olt,
                onu_uuid,
                root
            )

            if result:
                ticket_id = result.get("ticket_id")
                alarm_id = result.get("alarm_id")

                await create_alarm(
                    olt,
                    onu_uuid,
                    root.get("event"),
                    root.get("message"),
                    alarm_id=alarm_id
                )
            else:
                print("⚠️ Ticket duplicate")
                ticket_id = "-"
                alarm_id = f"INCIDENT-{olt.id}-{device_id}"

            root["alarm_id"] = alarm_id

            # =========================
            # TELEGRAM
            # =========================
            sample = ", ".join(map(str, incident.get("sample_devices", []))) or "-"

            text = f"""🚨 INCIDENT DETECTED

            OLT     : {olt.name}
            ROOT    : {device_id}
            EVENT   : {root.get('event')}

            IMPACT  : {incident['impact_count']} ONU
            Sample  : {sample}

            Time    : {datetime.now().strftime("%H:%M")}
            Ticket  : #{ticket_id}
            """

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

            print("📨 SEND TELEGRAM:", {
                "device": device_id,
                "alarm_id": alarm_id,
                "ticket": ticket_id
            })

            await bot.send_message(
                olt.client.telegram_chat_id,
                text,
                reply_markup=keyboard
            )

        except Exception as e:
            print("❌ INCIDENT ERROR:", e)

    # ===============================
    # 🔄 RECOVERY LOOP (UP ONLY)
    # ===============================
    for alert in alerts:

        if alert.get("status") != "UP":
            continue

        if alert.get("device_type") != "ONU":
            continue

        if not (
            alert.get("event") == "ONU_ONLINE"
            and not alert.get("is_root")
            and alert.get("root_label") == "ONU_OFFLINE"
        ):
            continue

        device_id = str(alert.get("device_id"))
        onu_uuid = onu_mapping.get(device_id)

        if not onu_uuid:
            continue

        print(f"🔄 Resolving ONU {device_id}")

        resolved = await resolve_alarm(
            olt,
            onu_uuid,
            "ONU_OFFLINE"
        )

        if not resolved:
            continue

        ticket_resolved = await TicketService.resolve_ticket(
            onu_uuid,
            "ONU_OFFLINE"
        )

        if ticket_resolved:
            resolved = ticket_resolved

        text = format_telegram(
            alert,
            olt.name,
            resolved=resolved
        )

        await bot.send_message(
            olt.client.telegram_chat_id,
            text
        )
        
        


# ===============================
# MAIN LOOP
# ===============================
async def monitoring_loop(bot):

    while True:

        print("---- MONITORING CYCLE ----", datetime.now())

        olts = await get_active_olts()

        tasks = [process_olt(bot, olt) for olt in olts]
        #await asyncio.gather(*tasks, return_exceptions=True)
        await asyncio.gather(*tasks)

        # ===============================
        # TOPOLOGY DETECTION
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
                        await bot.send_message(
                            chat_id=olt.client.telegram_chat_id,
                            text=text,
                            parse_mode="Markdown"
                        )

        await asyncio.sleep(30)
        
        
'''
👉 
bikin /api/incidents versi PRO (dengan grouping + severity + aging time)
'''
