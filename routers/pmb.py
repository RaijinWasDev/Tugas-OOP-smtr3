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
