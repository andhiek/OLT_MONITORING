# ========== state_cache.py ==========

from datetime import datetime

STATE = {
    "olts": {},
    "last_update": None
}

# 🔥 NEW
ACTIVE_INCIDENTS = {}  # key: device_id


def update_olt_state(olt_id, data):
    STATE["olts"][olt_id] = data
    STATE["last_update"] = datetime.now()
    


# 🔥 NEW FUNCTION
def process_alerts(alerts):
    for alert in alerts:
        device_id = alert.get("device_id")
        status = alert.get("status")

        if not device_id:
            continue

        # =============================
        # DOWN → ADD
        # =============================
        if status == "DOWN":
            ACTIVE_INCIDENTS[device_id] = alert

        # =============================
        # UP → REMOVE
        # =============================
        elif status == "UP":
            if device_id in ACTIVE_INCIDENTS:
                del ACTIVE_INCIDENTS[device_id]


def get_active_incidents():
    return list(ACTIVE_INCIDENTS.values())