from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy import text

from database import get_db
from routers.akses import require_admin

router = APIRouter()
WEB = Path(__file__).resolve().parents[1] / "web"


@router.get("/admin", include_in_schema=False)
def portal():
    return FileResponse(WEB / "admin.html")


@router.get("/admin/data", dependencies=[Depends(require_admin)])
def data_admin(db=Depends(get_db)):
    queries = {
        "pendaftar": "SELECT id, nama_lengkap, nim, status, program_studi_id, (SELECT COALESCE(SUM(sks),0) FROM matakuliah WHERE kode IN (SELECT d.kode_mk FROM krs k JOIN krs_detail d ON d.krs_id=k.id JOIN skala_nilai s ON s.huruf=d.nilai JOIN kurikulum u ON u.kode=d.kode_mk WHERE k.nim=m.nim AND u.prodi_id=m.program_studi_id AND k.status='approved' AND s.lulus=1)) sks_lulus FROM calon_mahasiswa m ORDER BY id DESC",
        "prodi": "SELECT id, nama FROM program_studi ORDER BY id",
        "jalur": "SELECT id, nama FROM jalur_masuk ORDER BY id",
        "kuliah": "SELECT m.kode,m.nama,m.sks,u.prodi_id,u.semester,p.nama kelompok FROM kurikulum u JOIN matakuliah m USING(kode) JOIN program_studi p ON p.id=u.prodi_id ORDER BY p.nama,u.semester,m.kode",
        "ruang": "SELECT kode, kapasitas FROM ruangan ORDER BY kode",
    }
    return {name: db.execute(text(query)).mappings().all() for name, query in queries.items()}



@router.get("/laporan-uml", include_in_schema=False)
def laporan_uml():
    return FileResponse(WEB.parent / "tugas/minggu_02_uml/Final-UML.pdf", media_type="application/pdf")


