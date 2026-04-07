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

            prev_root = cls._active_root_alarms.get(olt_id)

            root_alarm = None
            root_device_id = None
            root_label = None

            if down_alerts:
                sorted_alerts = sorted(
                    down_alerts,
                    key=lambda a: cls._priority(a),
                    reverse=True
                )

                # 🔥 PRIORITAS FIBER CUT
                fiber = [a for a in down_alerts if a.get("event") == "FIBER_CUT"]

                if fiber:
                    root_alarm = fiber[0]

                elif prev_root:
                    root_alarm = next(
                        (a for a in down_alerts if a["device_id"] == prev_root),
                        None
                    )

                    if not root_alarm:
                        root_alarm = sorted_alerts[0]

                else:
                    root_alarm = sorted_alerts[0]

                root_device_id = root_alarm["device_id"]
                cls._active_root_alarms[olt_id] = root_device_id
                
                root_label = root_alarm.get("event") if root_alarm else None
                

            else:
                # 🔥 semua UP → clear root
                cls._active_root_alarms.pop(olt_id, None)
            # =============================
            # 🔥 DEBUG DI SINI
            # =============================
            '''print(f"[CORRELATION] OLT {olt_id}")
            print(f"DOWN ALERTS: {len(down_alerts)}")
            print(f"DEVICES: {[a['device_id'] for a in olt_alerts]}")
            print(f"ROOT: {root_device_id}")
            print(f"ROOT LABEL: {root_label}")
            print("-" * 40)'''

            
            # =============================
            # BUILD RESULT
            # =============================
            for alert in olt_alerts:

                device_id = alert["device_id"]
                clean_msg = alert.get("message", "").lstrip("🚨 ").lstrip("✅ ")

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
                        "root_label": root_label,
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

        event = alert.get("event")
        device_type = alert.get("device_type")

        if event == "OLT_OFFLINE":
            score += 200

        elif event == "FIBER_CUT":
            score += 150

        elif device_type == "ONU":
            score += 50
            
            
        return score