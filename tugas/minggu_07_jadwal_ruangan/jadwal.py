from fastapi import APIRouter, Depends, HTTPException

from datetime import date
from tugas.minggu_08_perubahan_jadwal.kalender import export
from pydantic import BaseModel, Field
from sqlalchemy import text

from tugas.minggu_08_perubahan_jadwal.alternatif import Calendar, alternatives
from tugas.minggu_08_perubahan_jadwal.observer import schedule_changed, dispatch, retry_pending
from database import get_db
from routers.akses import require_admin

router = APIRouter()
ADMIN = [Depends(require_admin)]


class Slot(BaseModel):
    hari: int = Field(ge=1, le=7)
    mulai: int = Field(ge=0, lt=1440)
    selesai: int = Field(gt=0, le=1440)
    ruangan: str
    dosen: str = Field(min_length=1, max_length=80)


@router.get("/jadwal")
def daftar(db=Depends(get_db)):
    return db.execute(text("""SELECT j.*, m.hari, m.mulai, m.selesai, r.kapasitas
        FROM jadwal j JOIN matakuliah m USING(kode) JOIN ruangan r ON r.kode=j.ruangan
        ORDER BY m.hari, m.mulai, j.kode""")).mappings().all()


@router.get("/jadwal/konflik", dependencies=ADMIN)
def daftar_konflik(db=Depends(get_db)):
    pairs = []
    for row in daftar(db):
        for conflict in Calendar(db, row["kode"]).conflicts(row):
            if conflict["jadwal"][0] < conflict["jadwal"][1]:
                pairs.append(conflict)
    return pairs


def previous_slot(db, kode):
    return db.execute(text("""SELECT j.kode,j.ruangan,j.dosen,m.hari,m.mulai,m.selesai
        FROM jadwal j JOIN matakuliah m USING(kode) WHERE j.kode=:kode"""), {"kode": kode}).mappings().first()


@router.get("/jadwal/notifikasi", dependencies=ADMIN)
def notifications(db=Depends(get_db)):
    return db.execute(text("SELECT * FROM pesan_jadwal ORDER BY id DESC LIMIT 50")).mappings().all()


@router.get("/jadwal/kalender.ics", dependencies=ADMIN)
def calendar_export(awal: date, akhir: date, db=Depends(get_db)):
    return export(db, awal, akhir)


@router.post("/jadwal/outbox/retry", dependencies=ADMIN)
def retry_notifications(db=Depends(get_db)):
    retry_pending(db)
    return {"pending": db.scalar(text("SELECT count(*) FROM outbox_jadwal WHERE status='pending'"))}


@router.put("/jadwal/{kode}", dependencies=ADMIN)
def simpan(kode: str, slot: Slot, db=Depends(get_db)):
    data = slot.model_dump()
    data.update(kode=kode, dosen=slot.dosen.strip())
    if slot.mulai >= slot.selesai or not data["dosen"]:
        raise HTTPException(400, "Periksa nama dosen dan urutan jam")
    db.execute(text("BEGIN IMMEDIATE"))
    if not db.scalar(text("SELECT 1 FROM matakuliah WHERE kode=:kode"), data):
        raise HTTPException(404, "Mata kuliah tidak ditemukan")
    kapasitas = db.scalar(text("SELECT kapasitas FROM ruangan WHERE kode=:ruangan"), data)
    if kapasitas is None:
        raise HTTPException(404, "Ruangan tidak ditemukan")
    enrolled = db.scalar(text("""SELECT count(DISTINCT k.nim) FROM krs_detail d JOIN krs k
        ON k.id=d.krs_id WHERE d.kode_mk=:kode"""), data)
    calendar = Calendar(db, kode)
    conflicts = calendar.conflicts(data)
    if enrolled > kapasitas or conflicts:
        msg = (f"{enrolled} mahasiswa melebihi kapasitas {kapasitas}" if enrolled > kapasitas else
               "Jadwal bentrok dengan " + ", ".join(c["jadwal"][1] for c in conflicts))
        db.rollback()
        raise HTTPException(409, {"pesan": msg, "konflik": conflicts,
                                  "alternatif": alternatives(db, calendar, data, enrolled)})
    old = previous_slot(db, kode)
    if old == data:
        return data
    db.execute(text("UPDATE matakuliah SET hari=:hari, mulai=:mulai, selesai=:selesai WHERE kode=:kode"), data)
    db.execute(text("""INSERT INTO jadwal VALUES (:kode,:ruangan,:dosen)
        ON CONFLICT(kode) DO UPDATE SET ruangan=excluded.ruangan, dosen=excluded.dosen"""), data)
    message = f"{kode}: hari {slot.hari}, {slot.mulai//60:02}:{slot.mulai%60:02} di {slot.ruangan}, dosen {data['dosen']}."
    event_id = schedule_changed(db, kode, message, [old["dosen"], data["dosen"]] if old else [data["dosen"]])
    db.commit()
    dispatch(db, event_id)
    return data


@router.delete("/jadwal/{kode}", dependencies=ADMIN)
def hapus(kode: str, db=Depends(get_db)):
    db.execute(text("BEGIN IMMEDIATE"))
    old = previous_slot(db, kode)
    result = db.execute(text("DELETE FROM jadwal WHERE kode=:kode"), {"kode": kode})
    if not result.rowcount:
        raise HTTPException(404, "Jadwal tidak ditemukan")
    event_id = schedule_changed(db, kode, f"Jadwal {kode} dihapus.", [old["dosen"]])
    db.commit()
    dispatch(db, event_id)
    return {"dihapus": kode}
