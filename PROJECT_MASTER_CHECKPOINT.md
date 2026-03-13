# PROJECT MASTER CHECKPOINT

## Fiber Monitor – Mini ISP NMS

Checkpoint Version: **v0.1**
Date: **2026**

---

# 1. Project Overview

Fiber Monitor adalah sistem **Mini NMS (Network Monitoring System)** untuk ISP yang dibangun menggunakan Python.

Tujuan project:

- Monitoring perangkat jaringan (OLT / ONU)
- Alarm system untuk NOC
- Integrasi notifikasi Telegram
- Alarm acknowledge oleh operator
- Logging kejadian jaringan
- Sistem modular untuk dikembangkan menjadi NMS lengkap

Arsitektur mengikuti konsep NOC ISP sederhana.

---

# 2. Technology Stack

Backend:

- Python 3
- Async architecture

Database:

- PostgreSQL

ORM:

- SQLAlchemy (Async)

Migration:

- Alembic

Notification:

- Telegram Bot API

Scheduler:

- APScheduler

---

# 3. Project Folder Structure

Struktur project saat checkpoint ini:

```
fiber-monitor
│
├── app
│   ├── services
│   │   ├── alarm_service.py
│   │   ├── monitoring_service.py
│   │   └── device_service.py
│   │
│   ├── models
│   │   └── alarm.py
│   │
│   ├── database
│   │   └── db.py
│   │
│   └── telegram
│       ├── bot.py
│       └── handlers.py
│
├── simulator
│   └── olt_simulator.py
│
├── alembic
│
├── requirements.txt
│
├── CHECKPOINT_v0.1.md
├── PROJECT_MASTER_CHECKPOINT.md
└── checkpoint_alarm_engine.sql
```

---

# 4. Core System Architecture

Monitoring pipeline saat ini:

```
OLT Simulator
     │
     │
Monitoring Service
     │
     │
Alarm Engine
     │
     │
PostgreSQL Database
     │
     │
Telegram Notification
     │
     │
Operator ACK
```

---

# 5. Alarm Lifecycle

Sistem alarm mengikuti lifecycle standar NOC.

```
ACTIVE
  ↓
ACKNOWLEDGED
  ↓
CLEARED
```

Contoh flow:

```
ONU offline
↓
Alarm dibuat
↓
Operator acknowledge
↓
ONU kembali online
↓
Alarm cleared
```

---

# 6. Features Implemented (v0.1)

Status fitur saat checkpoint ini.

### Alarm Engine

✔ Alarm creation
✔ Alarm acknowledge
✔ Multi operator acknowledge
✔ Alarm timestamp logging

### Monitoring

✔ Monitoring cycle berjalan
✔ OLT simulator aktif
✔ ONU offline detection

### Database

✔ PostgreSQL database
✔ SQLAlchemy ORM
✔ Alembic migration

### Notification

✔ Telegram bot integration
✔ Telegram ACK button

---

# 7. Database Status

Database name:

```
noc_saas
```

Backup file:

```
checkpoint_alarm_engine.sql
```

Restore command:

```
sudo -u postgres psql noc_saas < checkpoint_alarm_engine.sql
```

---

# 8. Current Development Progress

Progress estimasi:

```
Foundation        ██████████████
Alarm Engine      ██████████████
Monitoring        ███████████░░░
Notification      █████████████░
Dashboard         ░░░░░░░░░░░░░░
```

Status:

```
Mini NMS Core: WORKING
```

---

# 9. Next Development Roadmap

Prioritas fitur berikutnya.

## v0.2

Alarm Deduplication

Tujuan:

Mencegah alarm duplikat jika device tetap offline.

Contoh:

BAD:

```
ONU offline
ONU offline
ONU offline
```

GOOD:

```
1 active alarm
```

---

## v0.3

Alarm Auto Clear

Jika device kembali normal.

Flow:

```
ONU offline
↓
Alarm active
↓
ONU online
↓
Alarm cleared
```

---

## v0.4

Alarm Severity

Level alarm:

```
CRITICAL
MAJOR
MINOR
WARNING
```

---

## v0.5

ONU Status Table

Untuk dashboard realtime:

- online
- offline
- rx power
- last seen

---

## v0.6

Telegram Alarm Summary

Contoh:

```
ACTIVE ALARMS: 12
UNACKED: 5
OLT ONLINE: 4
ONU ONLINE: 3120
```

---

## v0.7

Fiber Cut Detection

Logic:

```
IF >20 ONU offline
AND same PON
THEN FIBER CUT alarm
```

---

## v1.0

Mini ISP NMS

Target fitur:

- dashboard web
- topology map
- alarm correlation
- performance metrics

---

# 10. Recovery Instructions

Jika project ingin dijalankan ulang:

### 1. Install dependency

```
pip install -r requirements.txt
```

### 2. Start database

Pastikan PostgreSQL aktif.

### 3. Restore database

```
sudo -u postgres psql noc_saas < checkpoint_alarm_engine.sql
```

### 4. Run system

```
python main.py
```

---

# 11. Important Notes

Project ini dikembangkan sebagai **Mini ISP NMS platform**.

Checkpoint ini menandai:

```
v0.1 Alarm Engine Stable
```

Development selanjutnya dimulai dari:

```
Alarm Deduplication Engine
```

---

END OF CHECKPOINT
