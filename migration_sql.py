"""Revisi 001, SQLite. Urutan perintah menjadi bagian dari riwayat migrasi."""
UP = (
    """CREATE TABLE program_studi (
        id INTEGER PRIMARY KEY, kode TEXT NOT NULL UNIQUE CHECK(length(kode)=3),
        nama TEXT NOT NULL, fakultas TEXT NOT NULL)""",
    """CREATE TABLE jalur_masuk (
        id INTEGER PRIMARY KEY, nama TEXT NOT NULL UNIQUE
        CHECK(nama IN ('SNBP','SNBT','Mandiri')))""",
    """CREATE TABLE calon_mahasiswa (
        id INTEGER PRIMARY KEY, nama_lengkap TEXT NOT NULL, email TEXT COLLATE NOCASE NOT NULL UNIQUE,
        phone TEXT NOT NULL CHECK(phone GLOB '08[1-9]*' AND length(phone) BETWEEN 9 AND 13 AND phone NOT GLOB '*[^0-9]*'),
        tanggal_lahir DATE NOT NULL, alamat TEXT NOT NULL,
        program_studi_id INTEGER NOT NULL REFERENCES program_studi(id),
        jalur_masuk_id INTEGER NOT NULL REFERENCES jalur_masuk(id),
        status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected')),
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, approved_at DATETIME,
        nim TEXT UNIQUE)""",
    "INSERT INTO program_studi VALUES (1,'001','Teknik Informatika','Fakultas Teknik')",
    "INSERT INTO jalur_masuk VALUES (1,'SNBP'),(2,'SNBT'),(3,'Mandiri')",
)
DOWN = tuple("DROP TABLE " + name for name in ("calon_mahasiswa","jalur_masuk","program_studi"))

