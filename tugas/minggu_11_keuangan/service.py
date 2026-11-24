from datetime import date, timedelta
from email.message import EmailMessage
import logging
import os
import smtplib

from sqlalchemy import text
from database import SessionLocal


def generate(db, awal):
    params = dict(awal=awal, tempo=awal+timedelta(days=14))
    return db.execute(text("""INSERT INTO billing(nim,awal,tempo,pokok)
        SELECT m.nim,:awal,:tempo,CASE WHEN lower(p.fakultas) LIKE '%teknik%' THEN 5000000 ELSE 4000000 END
        FROM calon_mahasiswa m JOIN program_studi p ON p.id=m.program_studi_id WHERE m.status='approved'
        AND (lower(p.fakultas) LIKE '%teknik%' OR lower(p.fakultas) LIKE '%ekonomi%')
        ON CONFLICT(nim,awal) DO NOTHING"""),params).rowcount


def email_queue(db, key, nim, pesan):
    db.execute(text("""INSERT OR IGNORE INTO email_spp(id,penerima,pesan)
        SELECT :key,email,:pesan FROM calon_mahasiswa WHERE nim=:nim"""),locals())


def kirim_email(db):
    host=os.getenv("SPP_SMTP_HOST")
    if not host:
        return
    for row in db.execute(text("SELECT * FROM email_spp WHERE terkirim IS NULL ORDER BY rowid LIMIT 100")).all():
        msg=EmailMessage()
        msg["From"]=os.environ["SPP_SMTP_FROM"]
        msg["To"]=row.penerima
        msg["Subject"]="Pemberitahuan SPP"
        msg.set_content(row.pesan)
        with smtplib.SMTP(host,int(os.getenv("SPP_SMTP_PORT","587")),timeout=10) as smtp:
            smtp.starttls()
            if os.getenv("SPP_SMTP_USER"):
                smtp.login(os.environ["SPP_SMTP_USER"],os.environ["SPP_SMTP_PASSWORD"])
            smtp.send_message(msg)
        db.execute(text("UPDATE email_spp SET terkirim=CURRENT_TIMESTAMP WHERE id=:id"),{"id":row.id})
        db.commit()


def pekerjaan():
    today=date.today()
    awal=max(date(y,m,1) for y in (today.year-1,today.year) for m in (2,8) if date(y,m,1)<=today)
    with SessionLocal() as db:
        generate(db,awal)
        for b in db.execute(text("SELECT * FROM saldo_spp WHERE status='overdue'")):
            email_queue(db,f"reminder-{b.id}-{today:%Y-%W}",b.nim,f"Tagihan semester {b.awal} tersisa Rp{b.sisa}.")
        db.commit()
        kirim_email(db)


def mulai_jadwal():
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ModuleNotFoundError:
        return JadwalLokal()
    from datetime import datetime
    scheduler=BackgroundScheduler()
    scheduler.add_job(pekerjaan,"interval",minutes=5,next_run_time=datetime.now(),max_instances=1)
    scheduler.start()
    return scheduler
from threading import Event, Thread


class JadwalLokal:
    def __init__(self):
        self.stop = Event()
        self.thread = Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        while not self.stop.is_set():
            try:
                pekerjaan()
            except Exception:
                logging.exception("Pekerjaan SPP akan dicoba kembali.")
            self.stop.wait(300)

    def shutdown(self):
        self.stop.set()
        self.thread.join()

