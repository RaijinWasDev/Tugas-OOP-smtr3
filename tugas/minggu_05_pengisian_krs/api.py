from typing import Annotated
from fastapi import APIRouter,Depends,Path
from database import get_db
from tugas.minggu_05_pengisian_krs.pengisian import KRSManager

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

