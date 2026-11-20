from typing import Protocol

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from .gpa import hitung

router = APIRouter(prefix="/api/nilai", tags=["Nilai"])


class PresensiPort(Protocol):
    def persentase(self, nim: str, kode: str, semester: int) -> int: ...


class PresensiDemo:
    def persentase(self, nim, kode, semester):
        return 70 if kode == "ST101" else 100


class InputNilai(BaseModel):
    dosen: str
    huruf: str
    alasan: str = ""


sumber = """FROM krs k JOIN krs_detail d ON k.id=d.krs_id
    JOIN matakuliah m ON m.kode=d.kode_mk LEFT JOIN jadwal j ON j.kode=d.kode_mk
    LEFT JOIN skala_nilai s ON s.huruf=d.nilai WHERE k.status='approved'"""


@router.get("")
def daftar(db: Session = Depends(get_db), presensi: PresensiPort = Depends(PresensiDemo)):
    rows = db.execute(text("SELECT k.id,k.nim,k.semester,d.kode_mk,m.nama,d.nilai,j.dosen " + sumber +
                           " ORDER BY k.nim,k.semester,d.kode_mk")).mappings()
    return [dict(r, presensi=presensi.persentase(r.nim, r.kode_mk, r.semester)) for r in rows]


@router.get("/{nim}/{semester}")
def ringkasan(nim: str, semester: int, db: Session = Depends(get_db)):
    params = dict(nim=nim, semester=semester)
    rows = db.execute(text("SELECT k.semester,d.kode_mk,m.sks,s.bobot,s.lulus " + sumber +
                           " AND k.nim=:nim AND d.nilai IS NOT NULL"), params).mappings().all()
    ips, ipk = hitung(rows, semester)
    history = db.execute(text("""SELECT h.* FROM grade_history h JOIN krs k ON k.id=h.krs_id
        WHERE k.nim=:nim AND k.semester=:semester ORDER BY h.id DESC"""), params).mappings().all()
    return dict(ips=str(ips), ipk=str(ipk), riwayat=history)


@router.put("/{krs_id}/{kode}")
def simpan(krs_id: int, kode: str, data: InputNilai, db: Session = Depends(get_db),
           presensi: PresensiPort = Depends(PresensiDemo)):
    params = dict(id=krs_id, kode=kode, dosen=data.dosen.strip(), baru=data.huruf, alasan=data.alasan.strip())
    db.execute(text("BEGIN IMMEDIATE"))
    if not db.scalar(text("SELECT 1 FROM jadwal WHERE kode=:kode AND dosen=:dosen"), params):
        raise HTTPException(403, "Hanya dosen pengampu yang dapat mengisi nilai.")
    row = db.execute(text("SELECT k.nim,k.semester,d.nilai " + sumber +
                          " AND k.id=:id AND d.kode_mk=:kode"), params).first()
    if not row:
        raise HTTPException(404, "Mata kuliah tidak ditemukan pada KRS yang disetujui.")
    if presensi.persentase(row.nim, kode, row.semester) < 75:
        raise HTTPException(422, "Presensi kurang dari 75%.")
    bobot = db.scalar(text("SELECT bobot FROM skala_nilai WHERE huruf=:baru"), params)
    if bobot is None:
        raise HTTPException(422, "Nilai di luar skala.")
    if row.nilai != data.huruf:
        if row.nilai and not params["alasan"]:
            raise HTTPException(422, "Isi alasan koreksi nilai.")
        params.update(lama=row.nilai, bobot=bobot)
        db.execute(text("UPDATE krs_detail SET nilai=:baru,bobot=:bobot WHERE krs_id=:id AND kode_mk=:kode"), params)
        db.execute(text("""INSERT INTO grade_history(krs_id,kode_mk,lama,baru,dosen,alasan)
            VALUES (:id,:kode,:lama,:baru,:dosen,:alasan)"""), params)
    db.commit()
    return {"nilai": data.huruf}
