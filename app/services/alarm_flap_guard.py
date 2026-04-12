# ======== app/services/alarm_flap_guard.py =========

import time
from collections import defaultdict


class AlarmFlapGuard:
    """
    Anti-flapping protection:
    - DOWN cepat trigger (responsif)
    - UP butuh konfirmasi (anti spam recovery)
    - pakai sliding time window
    """

    _history = defaultdict(list)

    DOWN_THRESHOLD = 1   # langsung trigger
    UP_THRESHOLD = 1     # butuh 2x UP stabil
    TIME_WINDOW = 30     # detik

    # =============================
    # PUBLIC API
    # =============================

    @classmethod
    def should_trigger_down(cls, device_id, status):
        cls._record(device_id, status)

        recent = cls._get_recent(device_id)

        down_seq = cls._count_tail(recent, "DOWN")

        print(f"[FLAP] DOWN {device_id} seq={down_seq}")

        return down_seq >= cls.DOWN_THRESHOLD

    @classmethod
    def should_clear(cls, device_id, status):
        cls._record(device_id, status)

        recent = cls._get_recent(device_id)

        up_seq = cls._count_tail(recent, "UP")

        print(f"[FLAP] UP {device_id} seq={up_seq}")

        return up_seq >= cls.UP_THRESHOLD

    # =============================
    # INTERNAL
    # =============================

    @classmethod
    def _record(cls, device_id, status):
        now = time.time()

        cls._history[device_id].append({
            "status": status,
            "ts": now
        })

        cls._cleanup(device_id)

    @classmethod
    def _get_recent(cls, device_id):
        return [x["status"] for x in cls._history[device_id]]

    @classmethod
    def _cleanup(cls, device_id):
        now = time.time()

        cls._history[device_id] = [
            x for x in cls._history[device_id]
            if now - x["ts"] <= cls.TIME_WINDOW
        ]

    @staticmethod
    def _count_tail(sequence, target):
        """
        Hitung berapa kali status yang sama di bagian akhir
        contoh:
        [UP, DOWN, DOWN] → count_tail(DOWN) = 2
        """
        count = 0
        for s in reversed(sequence):
            if s == target:
                count += 1
            else:
                break
        return count