## =========== zte_c320.py ===========


from app.snmp.collector import SNMPCollector

class ZTEC320:

    OLT_STATUS_OID = "1.3.6.1.2.1.1.5.0"
    ONU_COUNT_OID = "1.3.6.1.2.1.2.1.0"

    def __init__(self, host, community="public"):
        self.client = SNMPCollector(host, community)

    async def get_olt_status(self):
        result = await self.client.get(self.OLT_STATUS_OID)
        return str(result) if result else "UNKNOWN" 

    async def get_onu_list(self):
        # sementara kosong sampai parser dibuat
        return []
    
    
    

