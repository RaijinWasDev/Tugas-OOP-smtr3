import json
import logging
from sqlalchemy import text
from tugas.minggu_06_persetujuan_krs.alur_krs import KRSWorkflow, KRSStatus

log = logging.getLogger(__name__)


class NotificationManager:
    def __init__(self):
        self.observers = []

    def attach(self, observer):
        if observer not in self.observers:
            self.observers.append(observer)

    def detach(self, observer):
        if observer in self.observers:
            self.observers.remove(observer)

    def notify(self, db, event):
        failures = []
        for observer in self.observers:
            try:
                with db.begin_nested():
                    observer.update(db, event)
            except Exception:
                failures.append(observer.role)
                log.exception("Notifikasi gagal untuk observer %s", observer.role)
        return failures


class NotificationObserver:
    def __init__(self, role, medium):
        self.role = role
        self.medium = medium

    def update(self, db, event):
        for recipient in sorted(event[self.role]):
            db.execute(text("""INSERT INTO pesan_jadwal(event_id,penerima,media,pesan)
                VALUES(:id,:recipient,:medium,:message) ON CONFLICT(event_id,media,penerima) DO NOTHING"""), {
                "id": event["id"], "recipient": recipient, "medium": self.medium, "message": event["message"]})


subject = NotificationManager()
for role, medium in [("students", "Email"), ("lecturers", "SMS"), ("admins", "Push")]:
    subject.attach(NotificationObserver(role, medium))


def schedule_changed(db, kode, message, lecturers):
    affected = db.execute(text("""SELECT k.id,k.nim,k.status FROM krs k JOIN krs_detail d
        ON k.id=d.krs_id WHERE d.kode_mk=:kode"""), {"kode": kode}).all()
    for row in affected:
        if row.status in ("approved", "submitted"):
            KRSWorkflow(db).apply_transition(row, KRSStatus.REVISION, "sistem", "sistem", message)
    event = {"students": sorted({r.nim for r in affected}), "lecturers": sorted(set(lecturers)),
             "admins": ["Admin Akademik"], "message": message}
    return db.execute(text("INSERT INTO outbox_jadwal(kode,payload) VALUES(:kode,:payload)"),
                      {"kode":kode,"payload":json.dumps(event)}).lastrowid


def dispatch(db, event_id):
    # SQLite serializes dispatchers; delivery logs and completion are committed together.
    with db.begin():
        db.execute(text("BEGIN IMMEDIATE"))
        row = db.execute(text("SELECT * FROM outbox_jadwal WHERE id=:id AND status='pending'"),
                         {"id":event_id}).mappings().first()
        if not row:
            return
        failures = subject.notify(db, dict(json.loads(row["payload"]), id=event_id))
        db.execute(text("""UPDATE outbox_jadwal SET status=:status,gagal=:failed,
            percobaan=percobaan+1 WHERE id=:id"""),
            {"id":event_id,"status":"pending" if failures else "sent","failed":", ".join(failures) or None})


def retry_pending(db):
    ids = db.execute(text("SELECT id FROM outbox_jadwal WHERE status='pending' ORDER BY id LIMIT 100")).scalars().all()
    db.commit()
    for event_id in ids:
        dispatch(db, event_id)
