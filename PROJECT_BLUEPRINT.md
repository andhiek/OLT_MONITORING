# Fiber Monitor – Project Blueprint

## 1. Project Goal

Build a lightweight ISP NOC Monitoring Platform focused on **Fiber OLT/ONU networks**.

Main objectives:

- Monitor OLT and ONU status via SNMP
- Detect ONU offline / power issues
- Store alarms with persistence
- Provide Telegram-based NOC alerting
- Detect network root cause (Fiber Cut, PON failure)

This project aims to evolve into a **Fiber Monitoring SaaS Platform for ISPs**.

---

# 2. System Architecture

```
OLT Device
   │
   ▼
SNMP Polling
   │
   ▼
Monitoring Engine
   │
   ▼
Alarm Engine
   │
   ▼
Alarm Persistence
   │
   ▼
Topology Engine
   │
   ▼
Root Cause Detection
   │
   ▼
Telegram NOC Bot
```

Monitoring interval:

```
default: 30 seconds
```

---

# 3. Database Schema

### clients

```
id
name
telegram_chat_id
```

### olts

```
id
client_id
name
host
community
brand
is_active
```

### splitters

```
id
olt_id
pon_port
name
```

### onus

```
id
olt_id
splitter_id
onu_index
serial_number
last_status
last_power
updated_at
```

### alarms

```
id
olt_id
onu_id
event_type
message
created_at
acknowledged_by
resolved_at
```

### status_logs

```
id
onu_id
status
power
timestamp
```

---

# 4. Monitoring Flow

```
scheduler.py
    │
    ▼
get_active_olts()
    │
    ▼
process_olt()
    │
    ▼
MonitoringService.get_status()
    │
    ▼
save_onu_data()
    │
    ▼
AlarmService.evaluate()
```

Alarm events produced:

```
ONU_OFFLINE
ONU_ONLINE
ONU_LOW_POWER
ONU_POWER_NORMAL
```

---

# 5. Alarm Lifecycle

```
ONU goes offline
        │
        ▼
create_alarm()
        │
        ▼
Telegram alert sent
        │
        ▼
Operator presses ACK
        │
        ▼
acknowledged_by stored
        │
        ▼
ONU back online
        │
        ▼
resolve_alarm()
        │
        ▼
Duration calculated
```

Example Telegram lifecycle:

```
🔴 ONU OFFLINE
🟡 ACKNOWLEDGED
🟢 RECOVERY
```

---

# 6. Topology Model

Topology structure:

```
OLT
 └── Splitter
       └── ONU
```

Example:

```
OLT-1
 └── PON 1/1/3
      └── SPL-03
           ├── ONU1
           ├── ONU2
           ├── ONU3
```

Stored in:

```
topology_service.py
```

---

# 7. Root Cause Detection

Root cause detection logic:

### Fiber Cut Detection

If:

```
down_onu / total_onu >= 70%
```

Then:

```
FIBER CUT SUSPECTED
```

Example alert:

```
🚨 FIBER CUT SUSPECTED

OLT : OLT-1
PON : 1/1/3
Splitter : SPL-03

ONU Down : 14 / 16
```

---

# 8. Telegram Bot

Telegram bot functions:

```
/start
/status
ACK button
```

Example alarm message:

```
🔴 [OLT-1]
ONU: 6
Status: OFFLINE
Time: 10:33

[ACK]
```

Recovery message:

```
🟢 [OLT-1]
ONU: 6
Status: BACK ONLINE
Duration: 00:14:22
```

---

# 9. Current Version Milestones

```
v0.1  alarm engine stable
v1.1  alarm persistence + ACK
v0.2  topology base
v1.2  root cause engine + fiber cut detection
```

Current project status:

```
Stable monitoring + topology-aware root cause detection
```

---

# 10. Future Roadmap

### Phase 1 – Monitoring Intelligence

- Alarm Correlation Engine
- PON Failure Detection
- OLT Unreachable Detection

### Phase 2 – NOC Automation

- Alarm suppression
- Alarm grouping
- Network summary dashboard

### Phase 3 – SaaS Platform

- Multi-client architecture
- Web dashboard
- Role-based access

---

# 11. Key Project Rules

Project scope must remain focused on:

```
Fiber ISP Monitoring
OLT / ONU monitoring
Root cause detection
NOC automation
```

Avoid turning this project into:

```
Generic network scanner
Random monitoring tools
Non-fiber monitoring
```

Goal:

```
Professional Fiber NOC Monitoring Platform
```
