# ======== app/services/alarm_correlation_service.py =========

from collections import defaultdict


class AlarmCorrelationService:

    _active_root_alarms = {}

    @classmethod
    def process(cls, alerts):

        if not alerts:
            return []

        results = []
        grouped = defaultdict(list)

        # =============================
        # GROUP BY OLT
        # =============================
        for alert in alerts:
            olt_id = alert.get("olt_id")
            grouped[olt_id].append(alert)

        # =============================
        # PROCESS PER OLT
        # =============================
        for olt_id, olt_alerts in grouped.items():

            # =============================
            # STEP 1: SORT BY PRIORITY
            # =============================
            sorted_alerts = sorted(
                olt_alerts,
                key=lambda a: cls._priority(a),
                reverse=True
            )

            root_alarm = sorted_alerts[0]
            root_device_id = root_alarm["device_id"]

            # =============================
            # STEP 2: STABILIZE ROOT
            # =============================
            prev_root = cls._active_root_alarms.get(olt_id)

            if prev_root:
                # kalau root lama masih ada di alert → pakai itu
                if any(a["device_id"] == prev_root for a in olt_alerts):
                    root_device_id = prev_root

            cls._active_root_alarms[olt_id] = root_device_id

            # =============================
            # STEP 3: BUILD RESULT
            # =============================
            for alert in olt_alerts:

                device_id = alert["device_id"]

                if device_id == root_device_id:
                    results.append({
                        **alert,
                        "is_root": True,
                        "root_cause_id": None,
                        "message": f"🚨 ROOT: {alert['message']}"
                    })
                else:
                    results.append({
                        **alert,
                        "is_root": False,
                        "root_cause_id": root_device_id,
                        "message": f"↳ CHILD of {root_device_id}: {alert['message']}"
                    })

        return results

    # =============================
    # PRIORITY LOGIC (IMPORTANT)
    # =============================
    @staticmethod
    def _priority(alert):

        msg = alert.get("message", "").lower()
        severity = alert.get("severity", "")

        score = 0

        # OLT lebih penting dari ONU
        if "olt" in msg:
            score += 100

        # severity weight
        if severity == "CRITICAL":
            score += 50
        elif severity == "MAJOR":
            score += 30
        elif severity == "MINOR":
            score += 10

        return score