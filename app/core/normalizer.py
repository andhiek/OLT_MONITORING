# ============ app/core/mormalizer.py ===========


def normalize_onu(onu: dict) -> dict:
    return {
        "id": onu.get("id"),
        "status": onu.get("status", "UNKNOWN"),
        "power": (
            float(onu["power"])
            if isinstance(onu.get("power"), (int, float))
            else None
        )
    }
