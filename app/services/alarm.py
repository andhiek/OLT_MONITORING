## ====== alarm.py ========


class AlarmService:

    POWER_LOW_THRESHOLD = -28
    POWER_RECOVER_THRESHOLD = -26  # hysteresis

    STATUS_STABLE_COUNT = 2
    POWER_STABLE_COUNT = 2

    previous_state = {}

    @classmethod
    def evaluate(cls, olt_id, data):
        alerts = []

        if olt_id not in cls.previous_state:
            cls.previous_state[olt_id] = {}

        olt_state = cls.previous_state[olt_id]

        # =========================
        # OLT CHECK (optional debounce bisa ditambah)
        # =========================
        olt_status = data.get("olt_status")
        prev_olt_status = olt_state.get("olt_status")

        if prev_olt_status and prev_olt_status != olt_status:
            if olt_status != "ONLINE":
                alerts.append("🚨 OLT OFFLINE!")
            else:
                alerts.append("✅ OLT BACK ONLINE")

        olt_state["olt_status"] = olt_status

        # =========================
        # ONU CHECK
        # =========================
        for onu in data.get("onu_list", []):

            key = f"onu_{onu['id']}"

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

            # -------------------------
            # STATUS DEBOUNCE
            # -------------------------
            if current_status != state["status"]:
                state["status_counter"] += 1

                if state["status_counter"] >= cls.STATUS_STABLE_COUNT:
                    state["status"] = current_status
                    state["status_counter"] = 0

                    if current_status == "OFFLINE":
                        alerts.append({
                            "event": "ONU_OFFLINE",
                            "onu_index": str(onu["id"]),
                            "message": f"🚨 ONU {onu['id']} OFFLINE"
                        })

                    elif current_status == "ONLINE":
                        alerts.append({
                            "event": "ONU_ONLINE",
                            "onu_index": str(onu["id"]),
                            "message": f"✅ ONU {onu['id']} ONLINE"
                        })
            else:
                state["status_counter"] = 0

            # -------------------------
            # POWER WITH HYSTERESIS
            # -------------------------
            if (
                current_status == "ONLINE"
                and isinstance(current_power, (int, float))
            ):

                if state["power_state"] == "NORMAL":

                    if current_power < cls.POWER_LOW_THRESHOLD:
                        state["power_counter"] += 1

                        if state["power_counter"] >= cls.POWER_STABLE_COUNT:
                            state["power_state"] = "LOW"
                            state["power_counter"] = 0

                            alerts.append({
                                "event": "ONU_LOW_POWER",
                                "onu_index": str(onu["id"]),
                                "message": f"📉 ONU {onu['id']} Redaman Tinggi ({current_power} dBm)"
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
                                "event": "ONU_POWER_NORMAL",
                                "onu_index": str(onu["id"]),
                                "message": f"✅ ONU {onu['id']} Redaman Normal ({current_power} dBm)"
                            })
                    else:
                        state["power_counter"] = 0

            state["power"] = current_power


        return alerts
