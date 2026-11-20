from datetime import date
from pydantic import BaseModel, ConfigDict, EmailStr, Field, PastDate

class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nama_lengkap: str = Field(min_length=3, pattern=r"\S")
    email: EmailStr
    phone: str = Field(pattern=r"^(\+62|62|0)8[1-9][0-9]{6,10}$")
    tanggal_lahir: PastDate
    alamat: str = Field(min_length=1, pattern=r"\S")
    program_studi_id: int = Field(gt=0)
    jalur_masuk_id: int = Field(gt=0)

class PendaftarOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nama_lengkap: str
    status: str
    nim: str | None

