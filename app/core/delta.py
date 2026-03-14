# ============= delta.py ==============

class DeltaProcessor:

    previous = {}
    POWER_TOLERANCE = 0.5  # dBm tolerance

    @classmethod
    def filter_changed(cls, olt_id, onu_list):

        if olt_id not in cls.previous:
            cls.previous[olt_id] = {}

        prev_map = cls.previous[olt_id]

        changed = []

        for onu in onu_list:

            key = onu["id"]
            prev = prev_map.get(key)

            if prev is None:
                # ONU pertama kali terlihat
                changed.append(onu)

            else:
                status_changed = prev.get("status") != onu.get("status")

                prev_power = prev.get("power")
                curr_power = onu.get("power")

                power_changed = False
                if prev_power is not None and curr_power is not None:
                    if abs(prev_power - curr_power) >= cls.POWER_TOLERANCE:
                        power_changed = True

                if status_changed or power_changed:
                    changed.append(onu)

            # update state
            prev_map[key] = onu

        return changed