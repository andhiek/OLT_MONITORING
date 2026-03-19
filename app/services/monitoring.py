# ======== app/services/monitoring.py =========

import os
from dotenv import load_dotenv

from app.core.normalizer import normalize_onu
from app.snmp.zte_simulator import ZTESimulator
from app.snmp.zte_c320 import ZTEC320

from app.services.alarm import AlarmService
from app.services.alarm_flap_guard import AlarmFlapGuard
from app.services.alarm_correlation_service import AlarmCorrelationService

from app.core.delta import DeltaProcessor

load_dotenv()


class MonitoringService:
    _simulators = {}

    def __init__(self, olt):
        """
        olt adalah object dari database (model OLT)
        """
        self.olt = olt
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
            # =============================
            # 1. FETCH DATA
            # =============================
            olt_status = await self.device.get_olt_status()
            onu_list = await self.device.get_onu_list()

            normalized = [normalize_onu(o) for o in onu_list]

            # =============================
            # 2. DELTA PROCESSOR
            # =============================
            changed_onu = DeltaProcessor.filter_changed(
                self.olt.id,
                normalized
            )

            print("TOTAL ONU:", len(normalized))
            print("CHANGED ONU:", len(changed_onu))

            # =============================
            # 3. ALARM ENGINE
            # =============================
            alerts = AlarmService.evaluate(
                self.olt.id,
                {
                    "olt_status": olt_status,
                    "onu_list": normalized
                }
            )
            print("RAW ALERTS:")
            for a in alerts:
                print(a)

            # =============================
            # 4. FLAP GUARD (ANTI FLAPPING)
            # =============================
            stable_alerts = []

            for a in alerts:
                device_id = a.get("device_id")
                status = a.get("status")  # 🔥 pakai ini, bukan message

                # ❌ kalau tidak ada device_id → skip (jangan dipakai)
                if not device_id:
                    continue

                if status == "DOWN":
                    if AlarmFlapGuard.should_trigger_down(device_id, "DOWN"):
                        stable_alerts.append(a)

                elif status == "UP":
                    if AlarmFlapGuard.should_clear(device_id, "UP"):
                        stable_alerts.append(a)

                else:
                    # DEGRADED / lainnya tetap lewat
                    stable_alerts.append(a) 

            # 🔥 FALLBACK (PENTING)
            if not stable_alerts and alerts:
                print("⚠️ Flap guard filtered all alerts, fallback to raw alerts")
                stable_alerts = alerts
                print("STABLE ALERTS:")
            for a in stable_alerts:
                print(a)

            # =============================
            # 5. CORRELATION ENGINE
            # =============================
            correlated_alerts = AlarmCorrelationService.process(stable_alerts)
            
            # =============================
            # 6. OUTPUT
            # =============================
            '''for a in correlated_alerts:
                print(a["message"])'''
            print("FINAL OUTPUT:")
            for a in correlated_alerts:
                print(a["message"], "| root:", a.get("is_root"))
            return {
                    "olt_id": self.olt.id,
                    "olt_status": olt_status,
                    "onu_list": normalized,
                    "alerts": correlated_alerts   # ⬅️ INI KUNCI
                }

        except Exception as e:
            return {
                    "olt_id": self.olt.id,
                    "olt_status": olt_status,
                    "onu_list": normalized,
                    "alerts": correlated_alerts   # ⬅️ INI KUNCI
                }