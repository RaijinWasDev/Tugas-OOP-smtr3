from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from tugas.minggu_03_pendaftaran_pmb.model import CalonMahasiswa, JalurMasuk, ProgramStudi

class EmailTerdaftar(Exception):
    pass

class ReferensiInvalid(Exception):
    pass

def register(db, data):
    values = data.model_dump()
    values["email"] = str(data.email).lower()
    phone = data.phone.lstrip("+")
    values["phone"] = "0" + phone[2:] if phone.startswith("62") else phone
    lookup = select(CalonMahasiswa.id).where(CalonMahasiswa.email == values["email"])
    if db.scalar(lookup) is not None:
        raise EmailTerdaftar
    for model, identifier in [(ProgramStudi, data.program_studi_id), (JalurMasuk, data.jalur_masuk_id)]:
        if db.get(model, identifier) is None:
            raise ReferensiInvalid(f"ID {model.__tablename__} tidak ditemukan")
    calon = CalonMahasiswa(**values)
    db.add(calon)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if db.scalar(lookup) is not None:
            raise EmailTerdaftar
        raise
    db.refresh(calon)
    return calon
