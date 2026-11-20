from fastapi import APIRouter, Depends, Header
from database import get_db
from tugas.minggu_05_pengisian_krs.api import Semester
router=APIRouter(prefix="/api/krs", tags=["KRS"])

from pydantic import BaseModel, Field
from tugas.minggu_06_persetujuan_krs.alur_krs import KRSWorkflow

class Versi(BaseModel):
    version: int = Field(ge=1)

class Revisi(Versi):
    catatan: str

@router.post("/{nim}/{semester}/submit")
def submit(nim:str,semester:Semester,data:Versi,x_nim:str=Header(),db=Depends(get_db)):
    return KRSWorkflow(db).submit_krs(nim,semester,x_nim,data.version)

@router.post("/{nim}/{semester}/approve")
def approve(nim:str,semester:Semester,data:Versi,x_dosen_pa:str=Header(),db=Depends(get_db)):
    return KRSWorkflow(db).approve_krs(nim,semester,x_dosen_pa,data.version)

@router.post("/{nim}/{semester}/revise")
def revise(nim:str,semester:Semester,data:Revisi,x_dosen_pa:str=Header(),db=Depends(get_db)):
    return KRSWorkflow(db).revise_krs(nim,semester,x_dosen_pa,data.version,data.catatan)
