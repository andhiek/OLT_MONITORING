
# ===== severity.py =====

SEVERITY_MAP = {
    "OLT_OFFLINE": "CRITICAL",
    "OLT_ONLINE": "INFO",

    "ONU_OFFLINE": "MAJOR",
    "ONU_ONLINE": "INFO",

    "ONU_LOW_POWER": "MINOR",
    "ONU_POWER_NORMAL": "INFO",
}


def get_severity(event):
    return SEVERITY_MAP.get(event, "INFO")