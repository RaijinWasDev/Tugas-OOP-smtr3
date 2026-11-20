from itertools import product
from random import Random
from types import SimpleNamespace
import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from test_krs import demo, action
from test_pmb import engine
from services.workflow import KRSWorkflow, check_transition, KRSStatus
from services.krs import KRSError, SKSValidator, ConflictValidator

@pytest.mark.parametrize("source,target,role",product(KRSStatus,KRSStatus,["mahasiswa","dosen"]))
def test_transitions(source,target,role):
    valid={( "draft","submitted","mahasiswa"),("revision","submitted","mahasiswa"),
           ("submitted","revision","dosen"),("submitted","approved","dosen"),("approved","revision","dosen")}
    if (source,target,role) in valid:
        check_transition(source,target,role)
    else:
        with pytest.raises(KRSError):check_transition(source,target,role)

def test_lifecycle_and_atomicity(demo):
    e,nim=demo
    v=action(demo,"add_course",1,"IF101")["version"]
    def move(method,*args):
        with Session(e) as db:
            return getattr(KRSWorkflow(db),method)(nim,1,*args)
    with pytest.raises(KRSError,match="berhak"):move("submit_krs","orang-lain",v)
    with pytest.raises(KRSError,match="Transisi"):move("approve_krs","PA01",v)
    submitted=move("submit_krs",nim,v)
    v=submitted["version"]
    with pytest.raises(KRSError,match="berhak"):move("approve_krs","PA02",v)
    with pytest.raises(KRSError,match="Catatan"):move("revise_krs","PA01",v,"   ")
    rev=move("revise_krs","PA01",v,"Tambahkan Basis Data")
    assert rev["catatan"]=="Tambahkan Basis Data"
    edit=action(demo,"add_course",1,"IF102")
    with pytest.raises(KRSError,match="Versi lama"):move("submit_krs",nim,rev["version"])
    v=move("submit_krs",nim,edit["version"])["version"]
    with e.begin() as c:
        c.exec_driver_sql("CREATE TRIGGER force_error BEFORE INSERT ON notifikasi BEGIN SELECT RAISE(ABORT,'test'); END")
    with pytest.raises(IntegrityError):move("approve_krs","PA01",v)
    with e.begin() as c:
        assert c.execute(text("SELECT status,approved_at,version FROM krs")).one()==("submitted",None,v)
        assert c.exec_driver_sql("SELECT count(*) FROM krs_log").scalar()==3
        c.exec_driver_sql("DROP TRIGGER force_error")
    assert move("approve_krs","PA01",v)["status"]=="approved"
    with pytest.raises(KRSError):action(demo,"remove_course",1,"IF101")
    reopened=move("reopen_krs","PA01",v+1,"Koreksi pilihan mata kuliah")
    assert reopened["status"]=="revision"
    with Session(e) as db:
        assert db.scalar(text("SELECT approved_at FROM krs")) is None
    edited=action(demo,"remove_course",1,"IF101")
    assert edited["total_sks"]==3
    submitted=move("submit_krs",nim,edited["version"])
    assert move("approve_krs","PA01",submitted["version"])["status"]=="approved"

def check_choices(choices):
    accepted=[]
    for i,(sks,hari,start,duration) in enumerate(choices):
        c=SimpleNamespace(kode=str(i),nama=str(i),sks=sks,hari=hari,mulai=start,selesai=start+duration)
        if SKSValidator().check(c,accepted,{}).passed and ConflictValidator().check(c,accepted,{}).passed:
            accepted.append(c)
    assert sum(c.sks for c in accepted)<=24
    slots=[(c.hari,t) for c in accepted for t in range(c.mulai,c.selesai)]
    assert len(slots)==len(set(slots))

def test_1000_reproducible():
    rng=Random(600)
    for _ in range(1000):
        check_choices([(rng.randint(1,4),rng.randint(1,5),rng.randint(8,17),rng.randint(1,3))
                       for _ in range(rng.randint(1,36))])
