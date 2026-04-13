# ======== app/services/incident_correlation_service.py =========

import time


class IncidentCorrelationService:

    _active_incidents = {}

    def process(self, alerts: list):

        if not alerts:
            return []

        incidents = {}

        # =============================
        # 🔥 STEP 1: CLEANUP RESOLVED INCIDENT
        # =============================
        active_keys = set()

        for alert in alerts:
            if alert.get("is_root") and alert.get("status") == "DOWN":
                key = f"{alert.get('olt_id')}-{alert.get('device_id')}"
                active_keys.add(key)

        # hapus incident yang sudah tidak aktif
        for key in list(self._active_incidents.keys()):
            if key not in active_keys:
                print(f"🧹 CLEAR INCIDENT: {key}")
                self._active_incidents.pop(key, None)

        # =============================
        # 🔥 STEP 2: BUILD / REUSE INCIDENT
        # =============================
        for alert in alerts:

            if not alert.get("is_root"):
                continue

            olt_id = alert.get("olt_id")
            root_id = alert.get("device_id")
            status = alert.get("status")

            # hanya DOWN yang bikin / maintain incident
            if status != "DOWN":
                continue

            key = f"{olt_id}-{root_id}"
            existing = self._active_incidents.get(key)

            # =============================
            # REUSE INCIDENT
            # =============================
            if existing:
                existing["is_new"] = False
                existing["last_seen"] = time.time()
                existing["root_alert"] = alert  # update alert terbaru
                incidents[key] = existing
                continue

            # =============================
            # NEW INCIDENT
            # =============================
            incident = {
                "incident_id": f"{key}-{int(time.time())}",
                "olt_id": olt_id,
                "root_device_id": root_id,
                "root_event": alert.get("event"),
                "root_alert": alert,
                "children": [],
                "impact_count": 0,
                "sample_devices": [],
                "is_new": True,
                "first_seen": time.time(),
                "last_seen": time.time(),
            }

            self._active_incidents[key] = incident
            incidents[key] = incident

        # =============================
        # 🔥 STEP 3: ATTACH CHILDREN
        # =============================
        for alert in alerts:

            if alert.get("is_root"):
                continue

            root_id = alert.get("root_cause_id")
            olt_id = alert.get("olt_id")

            key = f"{olt_id}-{root_id}"

            if key in incidents:
                incidents[key]["children"].append(alert)

        # =============================
        # 🔥 STEP 4: FINALIZE
        # =============================
        results = []

        for key, data in incidents.items():

            children = data.get("children", [])

            data["impact_count"] = len(children)
            data["sample_devices"] = [
                c.get("device_id") for c in children[:5]
            ]

            results.append(data)

        return results