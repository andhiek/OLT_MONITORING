## ======== zte_mock.py =======

import random

def get_olt_status():
    return "ONLINE"

def get_onu_stats():
    active = random.randint(10, 20)
    down = random.randint(0, 3)
    
    # simulasi redaman (dbm)
    power = round(random.uniform(-30, -15), 2)
    return active, down ,power
