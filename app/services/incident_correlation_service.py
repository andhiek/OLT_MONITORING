# ======== app/services/incident_correlation_service.py =========

import time


class IncidentCorrelationService:

    _active_incidents = {}

    def process(self, alerts: list):

        if not alerts:
            return []

        incidents = {}

        # =============================
        # 🔥 STEP 1: CLEANUP RESOLVED
        # =============================
        active_keys = set()

        for alert in alerts:
            if alert.get("is_root") and alert.get("status") == "DOWN":
                key = f"{alert.get('olt_id')}-{alert.get('device_id')}"
                active_keys.add(key)

        for key in list(self._active_incidents.keys()):
            if key not in active_keys:
                print(f"🧹 CLEAR INCIDENT: {key}")
                old = self._active_incidents.pop(key, None)
                if old:
                    old["is_active"] = False

        # =============================
        # 🔥 STEP 2: BUILD / REUSE
        # =============================
        for alert in alerts:

            if not alert.get("is_root"):
                continue

            if alert.get("status") != "DOWN":
                continue

            olt_id = alert.get("olt_id")
            root_id = alert.get("device_id")

            key = f"{olt_id}-{root_id}"
            existing = self._active_incidents.get(key)

            # =============================
            # REUSE
            # =============================
            if existing:
                existing["is_new"] = False
                existing["last_seen"] = time.time()
                existing["root_alert"] = alert
                existing["is_active"] = True
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
                "is_active": True,
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

        severity_map = {
            "CRITICAL": 4,
            "MAJOR": 3,
            "MINOR": 2,
            "INFO": 1
        }

        for key, data in incidents.items():

            children = data.get("children", [])

            # impact
            data["impact_count"] = len(children)

            # sample ONU
            data["sample_devices"] = [
                c.get("device_id") for c in children[:5]
            ]

            # aging (detik)
            data["age"] = int(time.time() - data["first_seen"])

            # severity aggregation
            all_alerts = [data["root_alert"]] + children

            max_sev = max(
                all_alerts,
                key=lambda x: severity_map.get(
                    x.get("severity", "INFO"), 1
                )
            )

            data["severity"] = max_sev.get("severity", "INFO")

            results.append(data)

        return results