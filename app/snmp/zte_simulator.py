# ========= app/snmp/zte_simulator.py =========


import random
import asyncio
from app.core.contracts import OLTDevice


class ZTESimulator(OLTDevice):

    ONU_TOTAL = 8

    def __init__(self):
        # Simpan state supaya tidak random total tiap polling
        self.onu_state = {}

        for i in range(1, self.ONU_TOTAL + 1):

            # Mapping ONU ke PON port
            pon_port = f"1/1/{((i-1)//4)+1}"

            self.onu_state[i] = {
                "status": "ONLINE",
                "power": round(random.uniform(-24, -20), 2),
                "pon_port": pon_port
            }

    async def get_olt_status(self):
        await asyncio.sleep(0.1)
        return "ONLINE"

    async def get_onu_list(self):
        await asyncio.sleep(0.4)

        onu_list = []

        for i in range(1, self.ONU_TOTAL + 1):

            state = self.onu_state[i]

            # ===== STATUS CHANGE (jarang) =====
            if random.random() < 0.05:  # 5% chance berubah
                if state["status"] == "ONLINE":
                    state["status"] = "OFFLINE"
                    state["power"] = None
                else:
                    state["status"] = "ONLINE"
                    state["power"] = round(random.uniform(-24, -20), 2)

            # ===== POWER DRIFT (pelan) =====
            if state["status"] == "ONLINE" and state["power"] is not None:
                drift = random.uniform(-0.5, 0.5)
                state["power"] = round(state["power"] + drift, 2)

                # batasi supaya tidak terlalu ekstrem
                state["power"] = max(-35, min(-15, state["power"]))

            onu_list.append({
                            "id": i,
                            "status": state["status"],
                            "power": state["power"],
                            "pon_port": state["pon_port"]
                        })

        return onu_list


