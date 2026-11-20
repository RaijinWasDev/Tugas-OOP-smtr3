from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas.pmb import PendaftarOut, RegisterRequest
from services.pmb import EmailTerdaftar, ReferensiInvalid, register

router = APIRouter(prefix="/api/pmb", tags=["PMB"])

@router.post("/register", status_code=201, response_model=PendaftarOut)
def daftar(data: RegisterRequest, db: Session = Depends(get_db)):
    try:
        return register(db, data)
    except EmailTerdaftar:
        raise HTTPException(409, "Email sudah terdaftar")
    except ReferensiInvalid as exc:
        raise HTTPException(400, str(exc))

from secrets import compare_digest
import os
from fastapi.security import APIKeyHeader
from services import approval

admin_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)

def require_admin(key: str | None = Depends(admin_header)):
    expected = os.environ.get("PMB_ADMIN_KEY")
    if not expected:
        raise HTTPException(503, "Kunci admin belum dikonfigurasi")
    if not key or not compare_digest(key.encode(), expected.encode()):
        raise HTTPException(403, "Akses admin diperlukan")

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
    return approval.stats(db)
