from fastapi import APIRouter
from datetime import datetime
from app.services.state_cache import STATE

router = APIRouter()


def calculate_severity(incident):
    """
    Determine severity based on:
    - root severity
    - impact count
    """

    root_sev = incident.get("root_alert", {}).get("severity", "INFO")
    impact = incident.get("impact_count", 0)

    if root_sev == "CRITICAL" or impact >= 5:
        return "CRITICAL"
    if impact >= 3:
        return "MAJOR"
    if impact >= 1:
        return "MINOR"

    return "INFO"


def calculate_aging(first_seen):
    """
    Convert timestamp → human readable duration
    """
    if not first_seen:
        return "0s"

    seconds = int(datetime.now().timestamp() - first_seen)

    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m"
    if seconds < 86400:
        return f"{seconds // 3600}h"

    return f"{seconds // 86400}d"


@router.get("/api/incidents")
async def get_incidents():

    raw_incidents = STATE.get("incidents", [])

    # =========================
    # 🔥 GROUP BY OLT
    # =========================
    grouped = {}

    for inc in raw_incidents:

        olt_id = str(inc.get("olt_id"))
        olt_name = inc.get("olt_name", "UNKNOWN")

        if olt_id not in grouped:
            grouped[olt_id] = {
                "olt_id": olt_id,
                "olt_name": olt_name,
                "total_incidents": 0,
                "critical": 0,
                "major": 0,
                "minor": 0,
                "incidents": []
            }

        severity = calculate_severity(inc)

        item = {
            "incident_id": inc.get("incident_id"),
            "root_device": inc.get("root_device_id"),
            "root_event": inc.get("root_event"),
            "severity": severity,
            "impact": inc.get("impact_count", 0),
            "sample": inc.get("sample_devices", []),
            "aging": calculate_aging(inc.get("first_seen")),
            "last_seen": int(inc.get("last_seen", 0)),
            "status": "ACTIVE",  # future: RESOLVED support
        }

        grouped[olt_id]["incidents"].append(item)
        grouped[olt_id]["total_incidents"] += 1

        if severity == "CRITICAL":
            grouped[olt_id]["critical"] += 1
        elif severity == "MAJOR":
            grouped[olt_id]["major"] += 1
        elif severity == "MINOR":
            grouped[olt_id]["minor"] += 1

    # =========================
    # 🔥 SORTING (IMPORTANT)
    # =========================
    for olt in grouped.values():
        olt["incidents"].sort(
            key=lambda x: (
                {"CRITICAL": 3, "MAJOR": 2, "MINOR": 1}.get(x["severity"], 0),
                x["impact"]
            ),
            reverse=True
        )

    # =========================
    # FINAL RESPONSE
    # =========================
    return {
        "total_olts": len(grouped),
        "total_incidents": len(raw_incidents),
        "data": list(grouped.values())
    }