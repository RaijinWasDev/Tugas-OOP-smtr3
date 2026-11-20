from sqlalchemy import select, func
from tugas.minggu_03_pendaftaran_pmb.model import CalonMahasiswa, ProgramStudi

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
