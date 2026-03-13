Checkpoint v0.1 – Alarm Engine Stable

Features:

- ONU simulator
- Monitoring cycle
- Alarm creation
- Alarm ACK
- Multi user ACK
- Alarm history in PostgreSQL

Next roadmap:

- Alarm deduplication
- Alarm clear
- Severity levels
- ONU status table
- Telegram notification

jika Jika suatu saat database rusak atau kamu ingin rollback:

sudo -u postgres psql -d noc_saas < checkpoint_alarm_engine.sql
