import asyncio
from pysnmp.hlapi.asyncio import (
    get_cmd,
    SnmpEngine,
    CommunityData,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity
)

class SNMPCollector:

    def __init__(self, host, community="public", port=161):
        self.host = host
        self.community = community
        self.port = port

    async def get(self, oid):
        errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
            SnmpEngine(),
            CommunityData(self.community),
            UdpTransportTarget((self.host,
                                self.port),
                                timeout=1.0,
                                retries=1), 
            ContextData(),
            ObjectType(ObjectIdentity(oid))
        )

        if errorIndication:
            raise Exception(errorIndication)

        elif errorStatus:
            raise Exception(str(errorStatus))

        else:
            for varBind in varBinds:
                return varBind[1]
