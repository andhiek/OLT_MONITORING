## ======== app/core/contracts.py =========

from abc import ABC, abstractmethod

class OLTDevice(ABC):

    @abstractmethod
    async def get_olt_status(self) -> str:
        pass

    @abstractmethod
    async def get_onu_list(self) -> list:
        pass
