# DEVELOPER GUIDE

## Fiber Monitor – Mini ISP NMS

Version: v0.1
Status: Alarm Engine Stable

---

# 1. Purpose of This Document

Dokumen ini menjelaskan cara kerja internal sistem **Fiber Monitor** agar developer dapat:

- memahami arsitektur sistem
- memahami alur monitoring
- memahami alarm engine
- melanjutkan development tanpa kebingungan

---

# 2. High Level Architecture

Sistem terdiri dari beberapa komponen utama.

Monitoring pipeline:

```
Network Device
     │
     │
Monitoring Engine
     │
     │
Alarm Engine
     │
     │
PostgreSQL Database
     │
     │
Notification Engine (Telegram)
     │
     │
NOC Operator
```

---

# 3. Core Components

## Monitoring Engine

Tugas:

- melakukan polling device
- membaca status device
- mendeteksi perubahan status

Contoh event yang dihasilkan:

```
ONU_OFFLINE
ONU_ONLINE
OLT_DOWN
OLT_UP
```

Monitoring engine akan mengirim event ke **Alarm Engine**.

---

## Alarm Engine

Alarm engine bertugas:

- membuat alarm baru
- menyimpan alarm ke database
- mengirim notifikasi
- menerima ACK dari operator

Lifecycle alarm:

```
ACTIVE
↓
ACKNOWLEDGED
↓
CLEARED
```

---

## Database Layer

Database utama menggunakan PostgreSQL.

ORM menggunakan SQLAlchemy async.

Contoh tabel utama:

### alarms

Fields utama:

```
id
device_id
alarm_type
severity
created_at
acknowledged_at
acknowledged_name
cleared_at
```

---

# 4. Alarm Flow

Contoh kejadian jaringan.

### Step 1

ONU kehilangan koneksi.

```
ONU 12 OFFLINE
```

Monitoring engine mendeteksi perubahan.

---

### Step 2

Monitoring mengirim event.

```
ONU_OFFLINE
```

---

### Step 3

Alarm Engine membuat alarm baru.

Database:

```
status = ACTIVE
created_at = timestamp
```

---

### Step 4

Notifikasi dikirim ke Telegram.

Contoh pesan:

```
🚨 CRITICAL ALARM

Device: OLT-1
ONU: 12
Status: OFFLINE
```

---

### Step 5

Operator melakukan acknowledge.

Melalui tombol Telegram.

Database update:

```
acknowledged_name
acknowledged_at
```

---

### Step 6 (future)

Jika ONU kembali online:

```
ONU_ONLINE
```

Alarm akan berubah menjadi:

```
CLEARED
```

---

# 5. Telegram Integration

Telegram bot digunakan sebagai interface operator NOC.

Fungsi utama:

- menerima alarm
- menampilkan tombol ACK
- mencatat operator yang acknowledge

Contoh tombol:

```
[ ACK ]
```

Ketika ditekan:

```
update alarms
set acknowledged_name = operator
```

---

# 6. Monitoring Cycle

Monitoring berjalan menggunakan scheduler.

Contoh interval:

```
60 seconds
```

Flow:

```
Scheduler trigger
↓
monitoring_service
↓
check device status
↓
send event to alarm engine
```

---

# 7. Simulator

Project menggunakan **OLT simulator** untuk testing.

Tujuan:

- mensimulasikan ONU online/offline
- testing alarm engine
- testing telegram alert

Simulator mengirim status ke monitoring engine.

---

# 8. Project Modules

Struktur module:

```
app/services
```

### monitoring_service.py

Fungsi:

- membaca status device
- menghasilkan event monitoring

---

### alarm_service.py

Fungsi:

- create alarm
- acknowledge alarm
- manage alarm lifecycle

---

### device_service.py

Fungsi:

- device status logic
- integrasi device

---

### telegram/bot.py

Fungsi:

- koneksi bot telegram
- kirim pesan alarm

---

### telegram/handlers.py

Fungsi:

- handle tombol ACK
- proses interaksi operator

---

# 9. Important Development Rules

Untuk menjaga stabilitas sistem.

Rule 1

Monitoring engine **tidak boleh langsung kirim telegram**.

Semua alarm harus melalui:

```
Alarm Engine
```

---

Rule 2

Alarm harus tersimpan di database sebelum dikirim.

---

Rule 3

Monitoring hanya menghasilkan **event**, bukan alarm.

---

# 10. Known Limitations (v0.1)

Sistem saat ini belum memiliki:

- alarm deduplication
- alarm auto clear
- alarm severity
- dashboard web
- fiber cut detection
- topology map

---

# 11. Next Development Priorities

Urutan pengembangan berikutnya.

### Priority 1

Alarm Deduplication

Tujuan:

mencegah alarm duplikat.

---

### Priority 2

Alarm Auto Clear

Alarm otomatis selesai jika device normal.

---

### Priority 3

Alarm Severity

Level alarm:

```
CRITICAL
MAJOR
MINOR
WARNING
```

---

### Priority 4

ONU Status Table

Digunakan untuk dashboard.

---

# 12. Developer Notes

Project ini dibangun sebagai **Mini ISP NMS**.

Target jangka panjang:

```
Full Network Monitoring Platform
```

Mirip sistem NMS profesional seperti:

- Zabbix
- LibreNMS

---

# 13. Current Stable Version

Checkpoint:

```
v0.1
```

Status:

```
Alarm Engine Stable
```

Development berikutnya dimulai dari:

```
Alarm Deduplication Engine
```

---

END OF DOCUMENT
