# NMS PROJECT ROADMAP

## Fiber Monitor – Mini ISP NMS

Project: Fiber Monitor
Language: Python
Architecture: Async Monitoring System

Current Version: **v0.1**

---

# Vision

Fiber Monitor dikembangkan menjadi **Mini Network Monitoring System (NMS)** untuk ISP yang mampu:

- memonitor perangkat jaringan
- mendeteksi gangguan jaringan
- mengelola alarm NOC
- memberikan notifikasi real-time
- menyediakan dashboard monitoring

Target jangka panjang adalah sistem yang konsepnya mirip platform monitoring seperti:

- Zabbix
- LibreNMS

---

# Development Philosophy

Project dikembangkan secara bertahap:

1. Bangun core system stabil
2. Tambahkan fitur monitoring
3. Tambahkan alarm intelligence
4. Tambahkan dashboard visual
5. Tambahkan network analytics

---

# VERSION ROADMAP

---

# v0.1 — Alarm Engine (CURRENT)

Status: **STABLE**

Fitur:

- Alarm creation
- Alarm acknowledge
- Telegram notification
- Telegram ACK button
- Monitoring simulator
- PostgreSQL database
- SQLAlchemy ORM
- Alembic migration

Pipeline sistem:

```
Monitoring → Alarm Engine → Database → Telegram
```

Checkpoint file:

```
checkpoint_alarm_engine.sql
```

---

# v0.2 — Alarm Deduplication

Tujuan:

mencegah alarm duplikat dari device yang sama.

Masalah saat ini:

```
ONU offline
ONU offline
ONU offline
```

Solusi:

```
1 ONU = 1 active alarm
```

Fitur:

- cek alarm aktif sebelum membuat alarm baru
- ignore duplicate alarm

Impact:

- database lebih bersih
- notifikasi tidak spam

---

# v0.3 — Alarm Auto Clear

Alarm otomatis selesai jika device kembali normal.

Flow:

```
ONU offline
↓
Alarm created
↓
Operator acknowledge
↓
ONU online
↓
Alarm cleared
```

Fitur:

- event ONU online
- update field `cleared_at`
- kirim notifikasi clear

---

# v0.4 — Alarm Severity System

Menambahkan level alarm.

Level:

```
CRITICAL
MAJOR
MINOR
WARNING
```

Contoh:

```
OLT_DOWN → CRITICAL
ONU_OFFLINE → MAJOR
RX_POWER_LOW → MINOR
```

---

# v0.5 — ONU Monitoring System

Monitoring detail ONU.

Field yang disimpan:

```
onu_id
olt_id
status
rx_power
tx_power
last_seen
```

Tujuan:

membuat status jaringan real-time.

---

# v0.6 — NOC Summary System

Bot dapat menampilkan ringkasan jaringan.

Contoh command Telegram:

```
/summary
```

Output:

```
ACTIVE ALARMS: 12
UNACKED: 5
OLT ONLINE: 8
ONU ONLINE: 3850
```

---

# v0.7 — Fiber Cut Detection

Fitur NOC penting.

Logic:

```
IF >20 ONU offline
AND same PON port
THEN fiber cut alarm
```

Alarm:

```
FIBER_CUT
```

---

# v0.8 — Dashboard API

Membuat REST API untuk dashboard.

Endpoint contoh:

```
/api/alarms
/api/devices
/api/onu-status
```

Tujuan:

menyiapkan backend untuk web UI.

---

# v0.9 — Network Topology

Visualisasi jaringan.

Contoh:

```
CORE
│
├── AGG SWITCH
│    │
│    └── OLT
│          │
│       SPLITTER
│      /   |   \
│    ONU  ONU  ONU
```

Status warna:

```
🟢 online
🟡 warning
🔴 critical
```

---

# v1.0 — Mini ISP NMS

Target akhir fase pertama.

Fitur:

- monitoring engine
- alarm engine
- telegram notification
- alarm correlation
- dashboard web
- topology map
- fiber cut detection
- device inventory

Sistem ini akan menjadi **Mini NOC Platform**.

---

# Future Possibilities

Setelah v1.0:

### AI Network Analytics

- anomaly detection
- predictive failure

### Performance Monitoring

- bandwidth monitoring
- traffic statistics

### Multi-OLT Support

monitor banyak OLT dari vendor berbeda.

---

# Development Strategy

Rule utama project:

Monitoring engine **tidak boleh langsung membuat alarm**.

Semua event harus melewati:

```
Alarm Engine
```

Tujuannya menjaga arsitektur modular.

---

# Current Development State

Version:

```
v0.1
```

Status:

```
Alarm Engine Stable
```

Next milestone:

```
v0.2 Alarm Deduplication
```

---

END OF ROADMAP
