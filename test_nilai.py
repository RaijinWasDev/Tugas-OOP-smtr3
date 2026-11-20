from itertools import product
from decimal import Decimal
import pytest

from tugas.minggu_09_nilai.gpa import hitung


def nilai(kode, bobot, sks=3, semester=1):
    return dict(kode_mk=kode, bobot=bobot, sks=sks, semester=semester, lulus=bobot>=2)


@pytest.mark.parametrize("rows,semester,ips,ipk", [
    ([],1,"0.00","0.00"),
    ([nilai("X",4)],1,"4.00","4.00"),
    ([nilai("X",0)],1,"0.00","0.00"),
    ([nilai("X",1)],1,"1.00","0.00"),
    ([nilai("X",0),nilai("X",3,semester=2)],2,"3.00","3.00"),
    ([nilai("X",4),nilai("X",2,semester=2)],2,"2.00","4.00"),
    ([nilai("X",2),nilai("Y",4),nilai("X",3,semester=2)],2,"3.00","3.50"),
    ([nilai("X",4,1),nilai("Y",3,4),nilai("Z",3,3)],1,"3.13","3.13"),
    ([nilai("X",4,1),nilai("Y",2,2)],1,"2.67","2.67"),
    ([nilai("X",4,semester=2)],1,"0.00","0.00"),
    ([nilai("X",2)],2,"0.00","2.00"),
    ([dict(nilai("X",1),lulus=True)],1,"1.00","1.00"),
])
def test_indeks(rows,semester,ips,ipk):
    assert hitung(rows,semester)==(Decimal(ips),Decimal(ipk))


def test_properti_ipk():
    for weights in product(range(5), repeat=4):
        rows=[nilai(str(i%3),w,1+i%3,1+i//3) for i,w in enumerate(weights)]
        _, ipk=hitung(rows,2)
        assert 0<=ipk<=4
        assert hitung(rows+[nilai("baru",4)],2)[1]>=ipk
        assert hitung(list(reversed(rows)),2)[1]==ipk


def test_input_dan_koreksi(tmp_path, monkeypatch):
    from alembic import command
    from alembic.config import Config
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    import database
    from main import app
    from test_pmb import enroll, approve

    engine=create_engine("sqlite:///"+(tmp_path/"nilai.db").as_posix())
    monkeypatch.setattr(database,"engine",engine)
    command.upgrade(Config("alembic.ini"),"head")
    nim=approve(engine,enroll(engine))[0]
    with engine.begin() as conn:
        conn.exec_driver_sql("INSERT INTO krs(id,nim,semester,status) VALUES(1,?,1,'approved')",(nim,))
        for kode in ["IF101","ST101"]:
            conn.exec_driver_sql("INSERT INTO krs_detail(krs_id,kode_mk) VALUES(1,?)",(kode,))
            conn.exec_driver_sql("INSERT INTO jadwal VALUES(?,'A101','Dosen Demo')",(kode,))
    def sesi():
        with Session(engine) as db:
            yield db
    monkeypatch.setitem(app.dependency_overrides,database.get_db,sesi)
    monkeypatch.setenv("PMB_ADMIN_KEY","demo")
    with TestClient(app,headers={"X-Admin-Key":"demo"}) as client:
        def simpan(kode,huruf,dosen="Dosen Demo",alasan=""):
            return client.put("/api/nilai/1/"+kode,json=dict(huruf=huruf,dosen=dosen,alasan=alasan))
        assert len(client.get("/api/nilai").json())==2
        assert simpan("ST101","B").status_code==422
        assert simpan("IF101","A","Dosen Lain").status_code==403
        assert simpan("IF101","B").status_code==200
        assert simpan("IF101","A").status_code==422
        assert simpan("IF101","A",alasan="Koreksi ujian").status_code==200
        result=client.get(f"/api/nilai/{nim}/1").json()
        assert result["ips"]==result["ipk"]=="4.00"
        assert [h["baru"] for h in result["riwayat"]]==["A","B"]
    engine.dispose()
