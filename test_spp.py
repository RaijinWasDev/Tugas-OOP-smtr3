import hashlib
import hmac
import json
from datetime import date, timedelta

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import database
from main import app
from test_pmb import enroll, approve


def test_spp_semester_webhook_dan_krs(tmp_path, monkeypatch):
    engine=create_engine("sqlite:///"+(tmp_path/"spp.db").as_posix())
    monkeypatch.setattr(database,"engine",engine)
    command.upgrade(Config("alembic.ini"),"head")
    nim=approve(engine,enroll(engine))[0]
    def sesi():
        with Session(engine) as db:
            yield db
    monkeypatch.setitem(app.dependency_overrides,database.get_db,sesi)
    monkeypatch.setenv("PMB_ADMIN_KEY","demo")
    monkeypatch.setenv("SPP_WEBHOOK_SECRET","test-key")
    c=TestClient(app,headers={"X-Admin-Key":"demo"})
    def generate(awal):
        return c.post("/api/spp/tagihan",params={"awal":awal}).json()["dibuat"]
    def report():
        return c.get("/api/spp/dashboard").json()
    assert generate(date.today())==1
    assert generate(date.today())==0
    assert report()["tagihan"][0]["status"]=="unpaid"
    assert c.post("/api/spp/bayar",json=dict(billing_id=1,amount=1,transaction_id="M")).status_code==200
    assert report()["tagihan"][0]["status"]=="partial"
    assert generate(date.today()-timedelta(days=90))==1
    assert report()["top"]==[{"nim":nim,"tunggakan":5050000}]
    from tugas.minggu_05_pengisian_krs.pengisian import KRSManager, KRSError
    import pytest
    with Session(engine) as db, pytest.raises(KRSError,match="SPP"):
        KRSManager(db).add_course(nim,1,"IF101")
    body=json.dumps(dict(billing_id=2,amount=5050000,transaction_id="G",status="success")).encode()
    def callback(signature):
        return c.post("/api/spp/webhook",content=body,headers={"X-Signature":signature})
    assert callback("salah").status_code==403
    signature=hmac.new(b"test-key",body,hashlib.sha256).hexdigest()
    assert callback(signature).status_code==callback(signature).status_code==200
    assert report()["top"]==[]
    assert report()["revenue"]==5050001
    with Session(engine) as db:
        assert KRSManager(db).add_course(nim,1,"IF101")["total_sks"]==3
    with engine.connect() as con:
        assert con.exec_driver_sql("SELECT COUNT(*) FROM email_spp").scalar()==2
    engine.dispose()
