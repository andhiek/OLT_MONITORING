# ============ app/core/normalizer.py ===========

def normalize_onu(onu: dict) -> dict:
    return {
        "id": onu.get("id"),
        "status": onu.get("status", "UNKNOWN"),
        "power": (
            float(onu["power"])
            if isinstance(onu.get("power"), (int, float))
            else None
        ),
        "pon_port": onu.get("pon_port") or onu.get("interface")
    }