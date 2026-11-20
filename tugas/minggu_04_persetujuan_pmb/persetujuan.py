from datetime import datetime, timezone
from sqlalchemy import select, func, text
from tugas.minggu_03_pendaftaran_pmb.model import CalonMahasiswa, ProgramStudi
from tugas.minggu_03_pendaftaran_pmb.validasi_pendaftar import RegisterRequest
from pydantic import ValidationError

class TidakDitemukan(Exception):
    pass

class TidakDapatDisetujui(Exception):
    pass

def status(db, id):
    row = db.get(CalonMahasiswa, id)
    if row is None:
        raise TidakDitemukan
    return row

def approve(db, id):
    # SQLite mengambil kunci tulis sebelum membaca nomor terakhir.
    with db.begin():
        db.execute(text("BEGIN IMMEDIATE"))
        row = status(db, id)
        if row.status == "approved" and row.nim:
            return row
        if row.status != "pending" or row.nim:
            raise TidakDapatDisetujui("Status pendaftar tidak dapat disetujui")
        try:
            RegisterRequest.model_validate(row, from_attributes=True)
        except ValidationError as exc:
            raise TidakDapatDisetujui("Data pendaftaran tidak lengkap atau tidak valid") from exc
        now = datetime.now(timezone.utc)
        prodi = db.get(ProgramStudi, row.program_studi_id)
        prefix = f"{now.year:04d}{prodi.kode}-"
        last = db.scalar(select(func.max(CalonMahasiswa.nim)).where(
            func.substr(CalonMahasiswa.nim, 1, len(prefix)) == prefix))
        number = int(last[-4:]) + 1 if last else 1
        if number > 9999:
            raise TidakDapatDisetujui("Nomor urut prodi untuk tahun ini sudah penuh")
        row.nim = f"{prefix}{number:04d}"
        row.status = "approved"
        row.approved_at = now
    return row
