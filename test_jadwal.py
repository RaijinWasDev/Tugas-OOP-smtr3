from importlib import import_module
from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi import HTTPException
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
from test_krs import demo, action
from test_pmb import engine
from tugas.minggu_07_jadwal_ruangan.jadwal import Slot, simpan, hapus


def test_change_conflict_and_notifications(demo):
    engine, nim = demo
    with engine.begin() as conn, Operations.context(MigrationContext.configure(conn)):
        for name in ["004_jadwal", "005_pesan", "006_outbox"]:
            import_module("migrations.versions." + name).upgrade()
    slot = Slot(hari=1, mulai=480, selesai=600, ruangan="A101", dosen="D01")
    with Session(engine) as db:
        simpan("IF101", slot, db)
    action(demo, "add_course", 1, "IF101")
    with engine.begin() as conn:
        conn.execute(text("UPDATE krs SET status='approved' WHERE nim=:nim"), {"nim":nim})
    with Session(engine) as db:
        with pytest.raises(HTTPException) as conflict:
            simpan("IF102", slot, db)
        db.rollback()
        detail=conflict.value.detail
        assert set(detail["konflik"][0]["types"])=={"room_conflict","lecturer_conflict","time_overlap"}
        assert len(detail["alternatif"])==3
        alternative=detail["alternatif"][0]
        simpan("IF102",Slot(**alternative),db)
        simpan("IF101",slot.model_copy(update={"dosen":"D02"}),db)
        assert db.scalar(text("SELECT status FROM krs"))=="revision"
        recipients=set(db.execute(text("SELECT penerima FROM pesan_jadwal")).scalars())
        assert {nim,"D01","D02","Admin Akademik"} <= recipients
        before=db.scalar(text("SELECT count(*) FROM pesan_jadwal"))
        db.rollback()
        simpan("IF101",slot.model_copy(update={"dosen":"D02"}),db)
        assert db.scalar(text("SELECT count(*) FROM pesan_jadwal"))==before
        db.rollback()
        hapus("IF101",db)
        assert db.scalar(text("SELECT count(*) FROM jadwal WHERE kode='IF101'"))==0

def test_outbox_rollback_retry_and_calendar(demo):
    from datetime import date
    from tugas.minggu_08_perubahan_jadwal.observer import subject, schedule_changed, dispatch
    from tugas.minggu_08_perubahan_jadwal.kalender import export

    engine, nim = demo
    with engine.begin() as conn, Operations.context(MigrationContext.configure(conn)):
        for name in ["004_jadwal", "005_pesan", "006_outbox"]:
            import_module("migrations.versions." + name).upgrade()
    class BrokenObserver:
        role = "rusak"
        def update(self, db, event):
            raise RuntimeError("simulasi")
    broken = BrokenObserver()
    subject.attach(broken)
    subject.attach(broken)
    try:
        assert subject.observers.count(broken)==1
        with Session(engine) as db:
            schedule_changed(db,"IF101","harus rollback",["D01"])
            db.rollback()
            assert db.scalar(text("SELECT count(*) FROM outbox_jadwal"))==0
            db.rollback()
            subject.observers.insert(0,subject.observers.pop())
            simpan("IF101",Slot(hari=1,mulai=480,selesai=600,ruangan="A101",dosen="D01"),db)
            event=db.execute(text("SELECT id,status,gagal FROM outbox_jadwal")).one()
            assert (event.status,event.gagal)==("pending","rusak")
            count=db.scalar(text("SELECT count(*) FROM pesan_jadwal"))
            assert count==2
            db.rollback()
            subject.detach(broken)
            dispatch(db,event.id)
            dispatch(db,event.id)
            assert db.scalar(text("SELECT count(*) FROM pesan_jadwal"))==count
            assert db.scalar(text("SELECT status FROM outbox_jadwal"))=="sent"
            result=export(db,date(2026,11,22),date(2026,12,31)).body.decode()
            assert "DTSTART:20261123T010000Z\r\n" in result
            assert "RRULE:FREQ=WEEKLY;UNTIL=20261231T165959Z" in result
            assert "UID:IF101-20261122@sevima-mini" in result
    finally:
        subject.detach(broken)


def test_ai_filters_unknown_room_and_conflicting_slot():
    from tugas.minggu_08_perubahan_jadwal.ai import select_suggestions
    valid=dict(hari=1,mulai=600,selesai=720,ruangan="A101",dosen="D01",kode="IF102")
    def fake(slot, available, model):
        return [dict(valid,reason="Jam tersedia"),dict(valid,ruangan="FIKTIF",reason="salah"),
                dict(valid,mulai=480,reason="sudah terisi")]
    assert select_suggestions({},[valid],fake)==[dict(valid,reason="Jam tersedia",sumber="AI")]
