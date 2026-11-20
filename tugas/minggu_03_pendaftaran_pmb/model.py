from datetime import date, datetime
from sqlalchemy import ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class ProgramStudi(Base):
    __tablename__ = "program_studi"
    id: Mapped[int] = mapped_column(primary_key=True)
    kode: Mapped[str] = mapped_column(String(3), unique=True)
    nama: Mapped[str]
    fakultas: Mapped[str]

class JalurMasuk(Base):
    __tablename__ = "jalur_masuk"
    id: Mapped[int] = mapped_column(primary_key=True)
    nama: Mapped[str] = mapped_column(unique=True)

class CalonMahasiswa(Base):
    __tablename__ = "calon_mahasiswa"
    id: Mapped[int] = mapped_column(primary_key=True)
    nama_lengkap: Mapped[str]
    email: Mapped[str] = mapped_column(String(collation="NOCASE"), unique=True)
    phone: Mapped[str]
    tanggal_lahir: Mapped[date]
    alamat: Mapped[str]
    program_studi_id: Mapped[int] = mapped_column(ForeignKey("program_studi.id"))
    jalur_masuk_id: Mapped[int] = mapped_column(ForeignKey("jalur_masuk.id"))
    status: Mapped[str] = mapped_column(server_default=text("'pending'"))
    created_at: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
    approved_at: Mapped[datetime | None]
    nim: Mapped[str | None] = mapped_column(unique=True)

