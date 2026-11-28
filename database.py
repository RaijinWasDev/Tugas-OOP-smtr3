from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# Menentukan lokasi file database.
DB_PATH = Path(__file__).resolve().parent / "akademik.db"

# Mengatur koneksi ke database SQLite.
engine = create_engine(
    f"sqlite:///{DB_PATH.as_posix()}",
    connect_args={"check_same_thread": False},
)


# Memastikan SQLite memeriksa hubungan antartabel.
@event.listens_for(engine, "connect")
def aktifkan_foreign_key(connection, connection_record):
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Membuat pengelola sesi database.
SessionLocal = sessionmaker(bind=engine)


# Kelas dasar untuk membuat model tabel.
class Base(DeclarativeBase):
    pass


# Menyediakan sesi database untuk endpoint API.
def get_db():
    with SessionLocal() as db:
        yield db