import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from migration_sql import UP, DOWN
from routers.pmb import daftar, cek_status, setujui, statistik, require_admin
from schemas.pmb import RegisterRequest
from main import app

@pytest.fixture
def engine(tmp_path):
    engine = create_engine("sqlite:///" + (tmp_path/"test.db").as_posix())
    with engine.begin() as con:
        for sql in UP:
            con.exec_driver_sql(sql)
    yield engine
    engine.dispose()

def data(**extra):
    raw = json.loads(Path(__file__).with_name("contoh.json").read_text())
    return RegisterRequest(**(raw | extra))

def enroll(engine, **extra):
    with Session(engine) as db:
        return daftar(data(**extra),db).id

def approve(engine, id):
    with Session(engine) as db:
        row = setujui(id,db)
        return row.nim, row.approved_at

def test_lifecycle(engine):
    a=enroll(engine)
    with Session(engine) as db:
        assert cek_status(a,db).status=="pending"
    n,t=approve(engine,a)
    assert n==f"{t.year}001-0001"
    assert approve(engine,a)==(n,t)
    assert approve(engine,enroll(engine,email="dua@example.com"))[0].endswith("0002")
    with Session(engine) as db:
        assert statistik(db)=={"total":2,"status":{"approved":2,"pending":0,"rejected":0},"per_prodi":{"001":{"approved":2,"pending":0,"rejected":0}}}

@pytest.mark.parametrize("change",[{"email":"invalid"},{"phone":"021123"}])
def test_format(change):
    with pytest.raises(ValidationError): data(**change)

def test_registration_errors(engine):
    enroll(engine)
    for changes,code in [({},409),({"email":"baru@example.com","program_studi_id":42},400)]:
        with pytest.raises(HTTPException) as e: enroll(engine,**changes)
        assert e.value.status_code==code

def test_invalid_approve(engine):
    a=enroll(engine)
    for sql in ["UPDATE calon_mahasiswa SET status='rejected'","UPDATE calon_mahasiswa SET status='pending',email='invalid'"]:
        with engine.begin() as con: con.execute(text(sql))
        with pytest.raises(HTTPException) as e: approve(engine,a)
        assert e.value.status_code==400
    for fn in [cek_status,setujui]:
        with Session(engine) as db,pytest.raises(HTTPException) as e: fn(999,db)
        assert e.value.status_code==404

@pytest.mark.parametrize("same",[True,False])
def test_concurrent(engine,same):
    first=enroll(engine)
    second=first if same else enroll(engine,email="dua@example.com")
    gate=threading.Barrier(2)
    def worker(i):
        gate.wait(timeout=10)
        return approve(engine,i)[0]
    with ThreadPoolExecutor(max_workers=2) as pool:
        numbers=list(pool.map(worker,[first,second]))
    assert sorted(n[-4:] for n in numbers)==(["0001","0001"] if same else ["0001","0002"])

def test_admin(monkeypatch):
    monkeypatch.delenv("PMB_ADMIN_KEY",raising=False)
    with pytest.raises(HTTPException) as e: require_admin(None)
    assert e.value.status_code==503
    monkeypatch.setenv("PMB_ADMIN_KEY","test-only")
    with pytest.raises(HTTPException) as e: require_admin("salah")
    assert e.value.status_code==403
    require_admin("test-only")

def test_swagger_contract():
    paths=app.openapi()["paths"]
    assert "201" in paths["/api/pmb/register"]["post"]["responses"]
    assert paths["/api/pmb/approve/{id}"]["put"]["security"]
    assert all("/api/pmb/"+s in paths for s in ("stats","status/{id}"))
