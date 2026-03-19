# ======== app/services/alarm_flap_guard.py =========

import time
from collections import defaultdict


class AlarmFlapGuard:
    """
    Anti-flapping protection:
    - DOWN harus stabil beberapa detik / cycle
    - UP juga harus stabil sebelum clear alarm
    """

    # history status per device
    _history = defaultdict(list)

    # config (bisa kamu pindah ke .env nanti)
    DOWN_THRESHOLD = 2   # berapa kali DOWN berturut-turut
    UP_THRESHOLD = 2     # berapa kali UP berturut-turut
    TIME_WINDOW = 120    # detik (opsional cleanup)

    @classmethod
    def should_trigger_down(cls, device_id, status):
        """
        Return True kalau status DOWN dianggap valid (bukan flapping)
        """

        cls._record(device_id, status)

        recent = cls._get_recent(device_id)

        # cek apakah DOWN stabil
        if len(recent) < cls.DOWN_THRESHOLD:
            return False

        if all(s == "DOWN" for s in recent[-cls.DOWN_THRESHOLD:]):
            return True

        return False

    @classmethod
    def should_clear(cls, device_id, status):
        """
        Return True kalau status UP dianggap stabil
        """

        cls._record(device_id, status)

        recent = cls._get_recent(device_id)

        if len(recent) < cls.UP_THRESHOLD:
            return False

        if all(s == "UP" for s in recent[-cls.UP_THRESHOLD:]):
            return True

        return False

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
        """
        buang history lama biar tidak makan memory
        """
        now = time.time()

        cls._history[device_id] = [
            x for x in cls._history[device_id]
            if now - x["ts"] <= cls.TIME_WINDOW
        ]