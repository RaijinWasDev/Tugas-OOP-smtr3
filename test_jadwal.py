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
        for name in ["004_jadwal", "005_pesan"]:
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
