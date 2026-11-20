from sqlalchemy import text


class NotificationManager:
    def __init__(self):
        self.observers = []

    def attach(self, observer):
        if observer not in self.observers:
            self.observers.append(observer)

    def detach(self, observer):
        self.observers.remove(observer)

    def notify(self, db, event):
        for observer in self.observers:
            observer.update(db, event)


class NotificationObserver:
    def __init__(self, role, medium):
        self.role = role
        self.medium = medium

    def update(self, db, event):
        for recipient in sorted(event[self.role]):
            db.execute(text("""INSERT INTO pesan_jadwal(penerima,media,pesan)
                VALUES(:recipient,:medium,:message)"""), {
                "recipient": recipient, "medium": self.medium, "message": event["message"]})


subject = NotificationManager()
for role, medium in [("students", "Email"), ("lecturers", "SMS"), ("admins", "Push")]:
    subject.attach(NotificationObserver(role, medium))


def schedule_changed(db, kode, message, lecturers):
    affected = db.execute(text("""SELECT k.id,k.nim,k.status FROM krs k JOIN krs_detail d
        ON k.id=d.krs_id WHERE d.kode_mk=:kode"""), {"kode": kode}).all()
    for row in affected:
        if row.status in ("approved", "submitted"):
            params = {"id": row.id, "old": row.status, "message": message}
            db.execute(text("""UPDATE krs SET status='revision',approved_at=NULL,
                version=version+1,catatan=:message WHERE id=:id"""), params)
            db.execute(text("""INSERT INTO krs_log(krs_id,asal,tujuan,aktor,catatan)
                VALUES(:id,:old,'revision','admin',:message)"""), params)
    subject.notify(db, {"students": {r.nim for r in affected}, "lecturers": set(lecturers),
                        "admins": {"Admin Akademik"}, "message": message})
