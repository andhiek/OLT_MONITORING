# ========== base.py ==========


from abc import ABC, abstractmethod

class BaseOLT(ABC):

    @abstractmethod
    def get_olt_status(self):
        pass

    @abstractmethod
    def get_onu_list(self):
        pass
