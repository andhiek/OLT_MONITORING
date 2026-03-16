# =========== topology_service.py ===========

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal as async_session
from app.db.models.olt import OLT
from app.db.models.splitter import Splitter

# =========================
# TOPOLOGY CACHE
# =========================

TOPOLOGY_CACHE = {}


async def load_topology():
    """
    Load topology from DB and store in cache
    """

    global TOPOLOGY_CACHE

    topology = {}

    async with async_session() as session:

        result = await session.execute(
            select(OLT).options(
                selectinload(OLT.splitters).selectinload(Splitter.onus)
            )
        )

        olts = result.scalars().all()

        for olt in olts:

            olt_id = str(olt.id)

            topology[olt_id] = {
                "name": olt.name,
                "splitters": {}
            }

            for splitter in olt.splitters:

                splitter_id = str(splitter.id)

                topology[olt_id]["splitters"][splitter_id] = {
                    "name": splitter.name,
                    "pon_port": splitter.pon_port,
                    "onus": []
                }

                for onu in splitter.onus:

                    topology[olt_id]["splitters"][splitter_id]["onus"].append({
                        "id": str(onu.id),
                        "onu_index": onu.onu_index,
                        "status": onu.last_status
                    })

    TOPOLOGY_CACHE = topology

    return topology


def get_cached_topology():
    return TOPOLOGY_CACHE


async def detect_fiber_cut(threshold=0.7):
    """
    Detect fiber cut using cached topology
    """

    alarms = []

    topology = get_cached_topology()

    for olt_id, olt_data in topology.items():

        for splitter_id, splitter_data in olt_data["splitters"].items():

            onus = splitter_data["onus"]

            if not onus:
                continue

            total_onu = len(onus)

            down_onu = sum(
                1 for onu in onus
                if onu["status"] == "down"
            )

            ratio = down_onu / total_onu

            if ratio >= threshold:

                alarms.append({
                    "type": "FIBER_CUT",
                    "olt_name": olt_data["name"],
                    "splitter_name": splitter_data["name"],
                    "pon_port": splitter_data["pon_port"],
                    "down_onu": down_onu,
                    "total_onu": total_onu
                })

    return alarms


async def detect_root_cause():

    topology = get_cached_topology()

    events = []

    for olt_id, olt_data in topology.items():

        for splitter_id, splitter_data in olt_data["splitters"].items():

            onus = splitter_data["onus"]

            if not onus:
                continue

            total = len(onus)

            down = sum(
                1 for onu in onus
                if onu["status"] == "down"
            )

            ratio = down / total

            # fiber cut detection
            if ratio >= 0.7:

                events.append({
                    "type": "fiber_cut",
                    "olt": olt_data["name"],
                    "splitter": splitter_data["name"],
                    "pon": splitter_data["pon_port"],
                    "down": down,
                    "total": total
                })

    return events