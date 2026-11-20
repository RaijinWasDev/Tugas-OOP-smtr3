from datetime import datetime, timezone
from sqlalchemy import select, func, text
from models.pmb import CalonMahasiswa, ProgramStudi
from schemas.pmb import RegisterRequest
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

def stats(db):
    counts = {"pending": 0, "approved": 0, "rejected": 0}
    prodi = {code: counts.copy() for code in db.scalars(select(ProgramStudi.kode))}
    groups = db.execute(select(ProgramStudi.kode, CalonMahasiswa.status, func.count())
        .join(CalonMahasiswa, CalonMahasiswa.program_studi_id == ProgramStudi.id)
        .group_by(ProgramStudi.kode, CalonMahasiswa.status))
    for code, state, count in groups:
        prodi[code][state] = count
        counts[state] += count
    return {"total": sum(counts.values()), "status": counts, "per_prodi": prodi}
