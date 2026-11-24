from datetime import datetime, timedelta
from io import BytesIO

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from openpyxl import load_workbook
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import database
from main import app
from test_pmb import enroll, approve
from tugas.minggu_12_presensi import api
from tugas.minggu_12_presensi.laporan import WIB


def test_siklus_presensi(tmp_path, monkeypatch):
    engine=create_engine("sqlite:///"+(tmp_path/"qr.db").as_posix())
    monkeypatch.setattr(database,"engine",engine)
    command.upgrade(Config("alembic.ini"),"head")
    nim=approve(engine,enroll(engine))[0]
    kedua=approve(engine,enroll(engine,email="kedua@example.com"))[0]
    with engine.begin() as c:
        c.exec_driver_sql("INSERT INTO jadwal VALUES('IF101','A101','Dosen Demo')")
        for i,n in enumerate([nim,kedua],1):
            c.exec_driver_sql("INSERT INTO krs(id,nim,semester,status) VALUES(?,?,1,'approved')",(i,n))
            c.exec_driver_sql("INSERT INTO krs_detail(krs_id,kode_mk) VALUES(?,'IF101')",(i,))
    def sesi():
        with Session(engine) as db:
            yield db
    monkeypatch.setitem(app.dependency_overrides,database.get_db,sesi)
    monkeypatch.setenv("PMB_ADMIN_KEY","demo")
    c=TestClient(app)
    headers={"X-Admin-Key":"demo"}
    start=datetime(2026,11,23,8,tzinfo=WIB)
    now=start
    monkeypatch.setattr(api,"sekarang",lambda:now)
    def qr():
        return c.get("/attendance/qr/IF101?semester=1&dosen=Dosen%20Demo",headers=headers)
    def scan(token,n):
        return c.post("/attendance/scan",json=dict(token=token,nim=n))
    def terbit():
        r=qr()
        assert r.status_code==200 and b"<svg" in r.content
        return r.headers["X-Scan-Link"].split("#")[1]
    token=terbit()
    assert scan(token,"lain").status_code==403
    assert scan(token,nim).json()["status"]=="hadir"
    assert scan(token,nim).status_code==409
    now=start+timedelta(minutes=15)
    assert scan(token,kedua).status_code==410
    baru=terbit()
    assert scan(token,kedua).status_code==410
    assert scan(baru,kedua).json()["status"]=="terlambat"
    now=start+timedelta(minutes=30)
    assert qr().status_code==409
    assert c.get("/attendance/report",headers=headers).json()["jumlah_berisiko"]==0
    for week in (1,2):
        now=start+timedelta(weeks=week)
        terbit()
    now+=timedelta(minutes=31)
    report=c.get("/attendance/report",headers=headers).json()
    assert report["jumlah_berisiko"]==2 and report["actions"]
    assert all(r["persen"]==33.33 for r in report["rekap"])
    book=load_workbook(BytesIO(c.get("/attendance/report.xlsx",headers=headers).content))
    assert book.active.max_row==3
    for _ in range(30):
        assert scan("salah",nim).status_code==410
    assert scan("salah",nim).status_code==429
    engine.dispose()
