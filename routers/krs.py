from routers.pmb import require_admin
from typing import Annotated
from fastapi import APIRouter,Depends,Path
from database import get_db
from services.krs import KRSManager

router=APIRouter(prefix="/api/krs",tags=["KRS"])
Semester=Annotated[int,Path(gt=0)]

@router.post("/{nim}/{semester}/mata-kuliah/{kode}",status_code=201)
def tambah(nim:str,semester:Semester,kode:str,db=Depends(get_db)):
    return KRSManager(db).add_course(nim,semester,kode)

@router.delete("/{nim}/{semester}/mata-kuliah/{kode}")
def hapus(nim:str,semester:Semester,kode:str,db=Depends(get_db)):
    return KRSManager(db).remove_course(nim,semester,kode)

@router.get("/{nim}/{semester}/validasi")
def validasi(nim:str,semester:Semester,db=Depends(get_db)):
    return KRSManager(db).validate_krs(nim,semester)

from fastapi import Header
from pydantic import BaseModel, Field
from services.workflow import KRSWorkflow

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

@router.post("/{nim}/{semester}/reopen", dependencies=[Depends(require_admin)])
def reopen(nim: str, semester: Semester, data: Revisi, x_dosen_pa: str = Header(), db=Depends(get_db)):
    return KRSWorkflow(db).reopen_krs(nim, semester, x_dosen_pa, data.version, data.catatan)
