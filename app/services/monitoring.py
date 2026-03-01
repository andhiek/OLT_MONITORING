# ======== app/services/monitoring.py =========


import os
from dotenv import load_dotenv
from app.core.normalizer import normalize_onu
from app.snmp.zte_simulator import ZTESimulator
from app.snmp.zte_c320 import ZTEC320

load_dotenv()

class MonitoringService:
    _simulators = {}

    def __init__(self, olt):
        """
        olt adalah object dari database (model OLT)
        """
        mode = os.getenv("MODE", "simulator")
        
        if mode == "real":
            self.device = ZTEC320(
                host=olt.host,
                community=olt.community,
            )
            print(f"🔵 Running REAL OLT: {olt.name} ({olt.host})")
        else:
            if olt.id not in self._simulators:
                self._simulators[olt.id] = ZTESimulator()
                
            self.device = self._simulators[olt.id]
            print(f"🟢 Running SIMULATOR for {olt.name}")

    async def get_status(self):
        try:
            olt_status = await self.device.get_olt_status()
            onu_list = await self.device.get_onu_list()

            normalized = [normalize_onu(o) for o in onu_list]

            return {
                "olt_status": olt_status,
                "onu_list": normalized,
            }

        except Exception as e:
            return {
                "olt_status": "ERROR",
                "onu_list": [],
                "error": str(e)
            }
