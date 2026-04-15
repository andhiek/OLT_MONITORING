# ======== app/services/monitoring.py =========

import os
from dotenv import load_dotenv

from app.services.state_cache import update_olt_state

from app.core.normalizer import normalize_onu
from app.snmp.zte_simulator import ZTESimulator
from app.snmp.zte_c320 import ZTEC320

from app.services.alarm import AlarmService
from app.services.alarm_flap_guard import AlarmFlapGuard
from app.services.alarm_correlation_service import AlarmCorrelationService
from app.services.state_cache import process_alerts
from app.services.ticket_service import TicketService
from app.services.state_cache import get_active_incidents


from app.core.delta import DeltaProcessor

load_dotenv()
print("🔥 ACTIVE INCIDENTS:", get_active_incidents())

class MonitoringService:
    _simulators = {}

    def __init__(self, olt):
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
                
                
            print("ONU LIST:")
            for o in normalized:
                print(f"ONU {o['id']} STATUS {o['status']}")

            # =============================
            # 4. FLAP GUARD
            # =============================
            stable_alerts = []

            for a in alerts:
                device_id = a.get("device_id")
                status = a.get("status")

                if not device_id:
                    continue

                if status == "DOWN":
                    if AlarmFlapGuard.should_trigger_down(device_id, "DOWN"):
                        stable_alerts.append(a)

                elif status == "UP":
                    if AlarmFlapGuard.should_clear(device_id, "UP"):
                        stable_alerts.append(a)

                else:
                    stable_alerts.append(a)

        

            print("STABLE ALERTS:")
            for a in stable_alerts:
                print(a)

            # =============================
            # 5. CORRELATION
            # =============================
            correlated_alerts = AlarmCorrelationService.process(stable_alerts)
            process_alerts(correlated_alerts)

            ''' # =============================
            # 6. CREATE TICKETS 🔥
            # =============================
            for alert in correlated_alerts:
                try:
                    if not alert.get("is_root"):
                        continue

                    if alert.get("status") != "DOWN":
                        continue

                    onu_id = alert.get("device_id")

                    print(f"🎯 Creating ticket for ONU {onu_id}")

                    await TicketService.create_ticket(
                        self.olt,
                        onu_id,
                        alert
                    )

                except Exception as e:
                    print("❌ Ticket creation error:", e)
                    # Kirim Telegram jika terjadi error saat pembuatan ticket
                    # Tapi pastikan OLT punya chat_id untuk menghindari error berantai
                    '''
            # =============================
            # 7. OUTPUT
            # =============================
            result = {
                "olt_id": self.olt.id,
                "olt_status": olt_status,
                "onu_list": normalized,
                "alerts": correlated_alerts
            }

            # 🔥 simpan ke cache
            update_olt_state(self.olt.id, result)

            return result
            
            
            

        except Exception as e:
            print("❌ Monitoring error:", e)

            fallback = {
                "olt_id": self.olt.id,
                "olt_status": {},
                "onu_list": [],
                "alerts": []
            }

            update_olt_state(self.olt.id, fallback)

            return fallback
        
        
        
        