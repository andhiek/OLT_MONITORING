# ====== app/services/alarm.py ========

class AlarmService:

    POWER_LOW_THRESHOLD = -28
    POWER_RECOVER_THRESHOLD = -26

    STATUS_STABLE_COUNT = 2
    POWER_STABLE_COUNT = 2

    previous_state = {}
    fiber_state = {}

    @classmethod
    def evaluate(cls, olt_id, data):

        alerts = []

        if olt_id not in cls.previous_state:
            cls.previous_state[olt_id] = {}

        olt_state = cls.previous_state[olt_id]

        # =============================
        # OLT CHECK
        # =============================
        olt_status = data.get("olt_status")
        prev_olt_status = olt_state.get("olt_status")

        if prev_olt_status and prev_olt_status != olt_status:

            if olt_status != "ONLINE":
                alerts.append({
                    "olt_id": olt_id,
                    "device_id": olt_id,
                    "device_type": "OLT",
                    "event": "OLT_OFFLINE",
                    "status": "DOWN",
                    "severity": "CRITICAL",
                    "message": f"🚨 OLT {olt_id} OFFLINE"
                })
            else:
                alerts.append({
                    "olt_id": olt_id,
                    "device_id": olt_id,
                    "device_type": "OLT",
                    "event": "OLT_RECOVERED",
                    "status": "UP",
                    "severity": "INFO",
                    "message": f"✅ OLT {olt_id} BACK ONLINE"
                })

        olt_state["olt_status"] = olt_status

        # =============================
        # ONU CHECK
        # =============================
        for onu in data.get("onu_list", []):
            

            onu_id = int(onu["id"])
            key = f"onu_{onu_id}"
            print(f"[CHECK] ONU {onu_id} RAW STATUS: {onu.get('status')}")

            if key not in olt_state:
                olt_state[key] = {
                    "status": onu.get("status"),
                    "power": onu.get("power"),
                    "status_counter": 0,
                    "power_counter": 0,
                    "power_state": "NORMAL"
                }
                continue

            state = olt_state[key]

            current_status = onu.get("status")
            current_power = onu.get("power")

            # =============================
            # STATUS DEBOUNCE
            # =============================
            if current_status != state["status"]:
                state["status_counter"] += 1

                if state["status_counter"] >= cls.STATUS_STABLE_COUNT:
                    state["status"] = current_status
                    state["status_counter"] = 0

                    if current_status == "OFFLINE":
                        alerts.append({
                            "olt_id": olt_id,
                            "device_id": onu_id,
                            "device_type": "ONU",
                            "event": "ONU_OFFLINE",
                            "status": "DOWN",
                            "severity": "MAJOR",
                            "message": f"🚨 ONU {onu_id} OFFLINE"
                        })

                    elif current_status == "ONLINE":
                        alerts.append({
                            "olt_id": olt_id,
                            "device_id": onu_id,
                            "device_type": "ONU",
                            "event": "ONU_ONLINE",
                            "status": "UP",
                            "severity": "INFO",
                            "message": f"✅ ONU {onu_id} ONLINE"
                        })

            else:
                state["status_counter"] = 0

            # =============================
            # POWER CHECK
            # =============================
            if current_status == "ONLINE" and isinstance(current_power, (int, float)):

                if state["power_state"] == "NORMAL":

                    if current_power < cls.POWER_LOW_THRESHOLD:
                        state["power_counter"] += 1

                        if state["power_counter"] >= cls.POWER_STABLE_COUNT:
                            state["power_state"] = "LOW"
                            state["power_counter"] = 0

                            alerts.append({
                                "olt_id": olt_id,
                                "device_id": onu_id,
                                "device_type": "ONU",
                                "event": "ONU_LOW_POWER",
                                "status": "DEGRADED",
                                "severity": "MINOR",
                                "message": f"📉 ONU {onu_id} Redaman Tinggi ({current_power} dBm)"
                            })

                    else:
                        state["power_counter"] = 0

                elif state["power_state"] == "LOW":

                    if current_power > cls.POWER_RECOVER_THRESHOLD:
                        state["power_counter"] += 1

                        if state["power_counter"] >= cls.POWER_STABLE_COUNT:
                            state["power_state"] = "NORMAL"
                            state["power_counter"] = 0

                            alerts.append({
                                "olt_id": olt_id,
                                "device_id": onu_id,
                                "device_type": "ONU",
                                "event": "ONU_POWER_NORMAL",
                                "status": "UP",
                                "severity": "INFO",
                                "message": f"✅ ONU {onu_id} Redaman Normal ({current_power} dBm)"
                            })

                    else:
                        state["power_counter"] = 0

            state["power"] = current_power

        # =============================
        # FIBER CUT DETECTION
        # =============================
        fiber_events = cls.detect_fiber_cut(olt_id, data.get("onu_list", []))
        alerts.extend(fiber_events)

        # =============================
        # ROOT CAUSE FILTER
        # =============================
        fiber_ports = {
            e["pon_port"]
            for e in fiber_events
            if e["event"] == "FIBER_CUT"
        }

        if fiber_ports:
            filtered = []

            for a in alerts:

                if a.get("event") in ["ONU_OFFLINE", "ONU_LOW_POWER"]:

                    onu_id = a.get("device_id")

                    pon = next(
                        (
                            o["pon_port"]
                            for o in data["onu_list"]
                            if int(o["id"]) == onu_id
                        ),
                        None
                    )

                    if pon in fiber_ports:
                        continue

                filtered.append(a)

            alerts = filtered

        return alerts

    # =============================
    # FIBER CUT DETECTOR
    # =============================
    @classmethod
    def detect_fiber_cut(cls, olt_id, onu_list):

        if olt_id not in cls.fiber_state:
            cls.fiber_state[olt_id] = {}

        olt_fiber = cls.fiber_state[olt_id]

        pon_map = {}

        for onu in onu_list:
            port = onu.get("pon_port")
            if not port:
                continue

            pon_map.setdefault(port, []).append(onu)

        events = []

        for port, onus in pon_map.items():

            offline = [o for o in onus if o["status"] == "OFFLINE"]
            offline_count = len(offline)

            prev_state = olt_fiber.get(port, "NORMAL")

            if offline_count >= 3:

                if prev_state != "CUT":
                    events.append({
                        "olt_id": olt_id,
                        "device_id": hash(f"{olt_id}-{port}"),
                        "device_type": "PON",
                        "event": "FIBER_CUT",
                        "status": "DOWN",
                        "severity": "CRITICAL",
                        "pon_port": port,
                        "count": offline_count,
                        "message": f"🚨 FIBER CUT DETECTED | PON {port} | ONU DOWN {offline_count}"
                    })

                    olt_fiber[port] = "CUT"

            else:

                if prev_state == "CUT":
                    events.append({
                        "olt_id": olt_id,
                        "device_id": hash(f"{olt_id}-{port}"),
                        "device_type": "PON",
                        "event": "FIBER_RESTORED",
                        "status": "UP",
                        "severity": "INFO",
                        "pon_port": port,
                        "count": offline_count,
                        "message": f"✅ FIBER RESTORED | PON {port}"
                    })

                    olt_fiber[port] = "NORMAL"

        return events