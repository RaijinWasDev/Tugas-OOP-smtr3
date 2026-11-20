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
        "pendaftar": "SELECT id, nama_lengkap, nim, status FROM calon_mahasiswa ORDER BY id DESC",
        "prodi": "SELECT id, nama FROM program_studi ORDER BY id",
        "jalur": "SELECT id, nama FROM jalur_masuk ORDER BY id",
        "kuliah": "SELECT kode, nama FROM matakuliah ORDER BY nama",
        "ruang": "SELECT kode, kapasitas FROM ruangan ORDER BY kode",
    }
    return {name: db.execute(text(query)).mappings().all() for name, query in queries.items()}
