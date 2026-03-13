# ============= delta.py ==============


class DeltaProcessor:

    previous = {}

    @classmethod
    def filter_changed(cls, olt_id, onu_list):

        if olt_id not in cls.previous:
            cls.previous[olt_id] = {}

        prev_map = cls.previous[olt_id]

        changed = []

        for onu in onu_list:

            key = onu["id"]

            prev = prev_map.get(key)

            if prev != onu:
                changed.append(onu)

            prev_map[key] = onu

        return changed