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
        # NORMALIZE DEVICE ID 🔥
        # =============================
        for alert in alerts:
            if alert.get("device_type") == "PON":
                pon = alert.get("pon_port")
                alert["device_id"] = f"PON-{pon}"

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
            # FILTER DOWN ALERTS (PRIORITY)
            # =============================
            down_alerts = [a for a in olt_alerts if a.get("status") == "DOWN"]

            # =============================
            # DETERMINE ROOT
            # =============================
            if down_alerts:
                sorted_alerts = sorted(
                    down_alerts,
                    key=lambda a: cls._priority(a),
                    reverse=True
                )
                root_alarm = sorted_alerts[0]
                root_device_id = root_alarm["device_id"]
                cls._active_root_alarms[olt_id] = root_device_id
            else:
                # 🔥 semua UP → clear root
                cls._active_root_alarms.pop(olt_id, None)
                root_device_id = None
                root_alarm = None

            prev_root = cls._active_root_alarms.get(olt_id)

            if prev_root and any(a["device_id"] == prev_root for a in olt_alerts):
                root_device_id = prev_root

            # =============================
            # BUILD RESULT
            # =============================
            for alert in olt_alerts:

                device_id = alert["device_id"]
                clean_msg = alert["message"].replace("🚨 ", "").replace("✅ ", "")

                if root_device_id and device_id == root_device_id:
                    results.append({
                        **alert,
                        "is_root": True,
                        "root_cause_id": None,
                        "message": f"🚨 ROOT: {clean_msg}"
                    })
                else:
                    results.append({
                        **alert,
                        "is_root": False,
                        "root_cause_id": root_device_id,
                        "root_label": root_alarm.get("event") if root_alarm else None,
                    })

        return results

    # =============================
    # PRIORITY LOGIC
    # =============================
    @staticmethod
    def _priority(alert):

        msg = alert.get("message", "").lower()
        severity = alert.get("severity", "")

        score = 0

        if "olt" in msg:
            score += 100

        if severity == "CRITICAL":
            score += 50
        elif severity == "MAJOR":
            score += 30
        elif severity == "MINOR":
            score += 10

        return score