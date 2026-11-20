import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session
from main import app
from database import get_db
from migration_sql import UP, DOWN

async def request(path, data=None):
    body = b"" if data is None else json.dumps(data).encode()
    scope = dict(type="http", asgi={"version":"3.0"}, http_version="1.1",
                 method="GET" if data is None else "POST", scheme="http", path=path,
                 raw_path=path.encode(), query_string=b"", root_path="",
                 headers=[(b"content-type", b"application/json")], server=("localhost",80),
                 client=("test",1))
    events = []
    received = False
    async def receive():
        nonlocal received
        if received:
            await asyncio.Event().wait()
        received = True
        return {"type":"http.request","body":body,"more_body":False}
    async def send(event):
        events.append(event)
    await app(scope, receive, send)
    return events[0]["status"], b"".join(e.get("body",b"") for e in events)

with TemporaryDirectory() as folder:
    engine = create_engine("sqlite:///" + Path(folder, "tes.db").as_posix())
    with engine.begin() as con:
        con.exec_driver_sql("PRAGMA foreign_keys=ON")
        for sql in UP + DOWN:
            con.exec_driver_sql(sql)
        assert not inspect(con).get_table_names()
        for sql in UP:
            con.exec_driver_sql(sql)
        assert len(inspect(con).get_table_names()) == 3
    print("SQL upgrade, downgrade dan upgrade ulang berhasil")
    def session_tes():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[get_db] = session_tes
    data = json.loads(Path(__file__).with_name("contoh.json").read_text())
    try:
        for changes, expected in [({},201),({},409),({"phone":"021123"},400),({"email":"invalid"},400),({"email":"baru@example.com","program_studi_id":99},400)]:
            status,body = asyncio.run(request("/api/pmb/register",data|changes))
            assert status == expected,(status,body)
            if expected==201: assert json.loads(body)["status"]=="pending" and json.loads(body)["nim"] is None
            print(status,body.decode())
        assert asyncio.run(request("/docs"))[0]==200
        print("Swagger UI tersedia")
    finally:
        app.dependency_overrides.clear()
        engine.dispose()

