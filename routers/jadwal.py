from fastapi import APIRouter, Depends, HTTPException

from pydantic import BaseModel, Field
from sqlalchemy import text

from database import get_db
from routers.pmb import require_admin

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


def detect_schedule_conflict(db, data):
    rows = db.execute(text("""SELECT j.kode, j.ruangan, j.dosen FROM matakuliah m
        JOIN jadwal j USING(kode) WHERE m.kode != :kode AND m.hari=:hari
        AND m.mulai < :selesai AND :mulai < m.selesai ORDER BY j.kode"""), data)
    conflicts = []
    for row in rows:
        types = []
        if row.ruangan == data["ruangan"]:
            types.append("room_conflict")
        if row.dosen.casefold() == data["dosen"].casefold():
            types.append("lecturer_conflict")
        if types:
            conflicts.append({"types": ["time_overlap", *types], "jadwal": [data["kode"], row.kode]})
    return conflicts


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
    if enrolled > kapasitas:
        raise HTTPException(409, f"{enrolled} mahasiswa melebihi kapasitas {kapasitas}")
    conflicts = detect_schedule_conflict(db, data)
    if conflicts:
        raise HTTPException(409, conflicts)
    db.execute(text("UPDATE matakuliah SET hari=:hari, mulai=:mulai, selesai=:selesai WHERE kode=:kode"), data)
    db.execute(text("""INSERT INTO jadwal VALUES (:kode,:ruangan,:dosen)
        ON CONFLICT(kode) DO UPDATE SET ruangan=excluded.ruangan, dosen=excluded.dosen"""), data)
    db.commit()
    return data


@router.delete("/jadwal/{kode}", dependencies=ADMIN)
def hapus(kode: str, db=Depends(get_db)):
    result = db.execute(text("DELETE FROM jadwal WHERE kode=:kode"), {"kode": kode})
    if not result.rowcount:
        raise HTTPException(404, "Jadwal tidak ditemukan")
    db.commit()
    return {"dihapus": kode}
