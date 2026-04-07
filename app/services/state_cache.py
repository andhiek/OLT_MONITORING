# ========== state_cache.py ==========

from datetime import datetime

STATE = {
    "olts": {},   # key: olt_id
    "last_update": None
}


def update_olt_state(olt_id, data):
    STATE["olts"][olt_id] = data
    STATE["last_update"] = datetime.now()