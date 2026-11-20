from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from tugas.minggu_03_pendaftaran_pmb.validasi_pendaftar import PendaftarOut
from routers.akses import require_admin
from . import persetujuan as approval
from .statistik import stats

router = APIRouter(prefix="/api/pmb", tags=["PMB"])

@router.get("/status/{id}", response_model=PendaftarOut)
def cek_status(id: int, db: Session = Depends(get_db)):
    try:
        return approval.status(db, id)
    except approval.TidakDitemukan:
        raise HTTPException(404, "Pendaftar tidak ditemukan")

@router.put("/approve/{id}", response_model=PendaftarOut, dependencies=[Depends(require_admin)])
def setujui(id: int, db: Session = Depends(get_db)):
    try:
        return approval.approve(db, id)
    except approval.TidakDitemukan:
        raise HTTPException(404, "Pendaftar tidak ditemukan")
    except approval.TidakDapatDisetujui as exc:
        raise HTTPException(400, str(exc))

@router.get("/stats")
def statistik(db: Session = Depends(get_db)):
    return stats(db)
