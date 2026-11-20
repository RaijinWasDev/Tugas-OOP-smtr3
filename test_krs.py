import importlib.util
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from sqlalchemy.orm import Session
from sqlalchemy import text
import pytest
from test_pmb import engine, enroll, approve
from tugas.minggu_05_pengisian_krs.pengisian import KRSManager, KRSError, MISSING

@pytest.fixture
def demo(engine):
    spec=importlib.util.spec_from_file_location("krs_migration","migrations/versions/002_krs.py")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    with engine.begin() as conn:
        from alembic.operations import Operations
        from alembic.migration import MigrationContext
        with Operations.context(MigrationContext.configure(conn)):
            mod.upgrade()
            next_spec=importlib.util.spec_from_file_location("workflow_migration","migrations/versions/003_workflow.py")
            workflow=importlib.util.module_from_spec(next_spec)
            next_spec.loader.exec_module(workflow)
            workflow.upgrade()
    nim=approve(engine,enroll(engine))[0]
    return engine,nim

def action(demo,method,*args):
    engine,nim=demo
    with Session(engine) as db:
        return getattr(KRSManager(db),method)(nim,*args)

def test_demo(demo):
    assert action(demo,"add_course",2,"IF101")["total_sks"]==3
    for code,msg in [("ST101","bentrok"),("IF201","kelulusan"),("IF101","sudah dipilih")]:
        with pytest.raises(KRSError,match=msg):action(demo,"add_course",2,code)
    assert action(demo,"add_course",2,"IF102")["total_sks"]==6
    assert action(demo,"validate_krs",2)["valid"]
    assert action(demo,"remove_course",2,"IF102")["total_sks"]==3

def test_grade_and_edit_state(demo):
    e,nim=demo
    action(demo,"add_course",1,"IF101")
    with e.begin() as c:
        c.exec_driver_sql("UPDATE krs SET status='approved'")
        c.exec_driver_sql("UPDATE krs_detail SET bobot=1")
    with pytest.raises(KRSError):action(demo,"remove_course",1,"IF101")
    with pytest.raises(KRSError):action(demo,"add_course",2,"IF201")
    with e.begin() as c:c.exec_driver_sql("UPDATE krs_detail SET bobot=2")
    assert action(demo,"add_course",2,"IF201")["total_sks"]==3
    with e.begin() as c:
        c.exec_driver_sql("UPDATE krs SET status='revision' WHERE semester=2")
        c.exec_driver_sql("UPDATE krs_detail SET bobot=1 WHERE kode_mk='IF101'")
    assert not action(demo,"validate_krs",2)["valid"]
    assert action(demo,"remove_course",2,"IF201")["status"]=="revision"

def test_two_requests_from_21_sks(demo):
    e,nim=demo
    with e.begin() as c:
        for n in range(9):
            c.exec_driver_sql("INSERT INTO matakuliah VALUES(?,?,3,3,?,?)",(str(n),str(n),60*n,60*n+60))
    for n in range(7):action(demo,"add_course",1,str(n))
    gate=Barrier(2)
    def attempt(code):
        gate.wait(timeout=8)
        try:return action(demo,"add_course",1,code)["total_sks"]
        except KRSError as exc:return str(exc)
    with ThreadPoolExecutor(2) as pool: results=list(pool.map(attempt,["7","8"]))
    assert 24 in results and "Total 27 SKS melebihi batas 24" in results
    assert action(demo,"validate_krs",1)["total_sks"]==24

