from alembic import op

revision = "010_katalog"
down_revision = "009_presensi"

KATALOG = [
    ("TI103", "Pemrograman Berorientasi Objek", 3, 3, 480, 600),
    ("TI104", "Jaringan Komputer", 3, 4, 600, 720),
    ("TI105", "Sistem Operasi", 3, 5, 480, 600),
    ("TI106", "Kecerdasan Buatan", 3, 2, 600, 720),
    ("SI101", "Pengantar Sistem Informasi", 3, 1, 780, 900),
    ("SI102", "Analisis dan Perancangan Sistem", 3, 3, 600, 720),
    ("SI103", "Pemodelan Proses Bisnis", 3, 4, 480, 600),
    ("SI104", "Manajemen Proyek Sistem Informasi", 3, 5, 600, 720),
]

def upgrade():
    conn = op.get_bind()
    if not conn.exec_driver_sql("SELECT 1 FROM program_studi WHERE lower(nama)='sistem informasi'").first():
        used = set(conn.exec_driver_sql("SELECT kode FROM program_studi").scalars())
        kode = next(f"{i:03}" for i in range(2,1000) if f"{i:03}" not in used)
        conn.exec_driver_sql("INSERT INTO program_studi(kode,nama,fakultas) VALUES(?,'Sistem Informasi','Fakultas Teknik')",(kode,))
    conn.exec_driver_sql("""INSERT INTO matakuliah(kode,nama,sks,hari,mulai,selesai)
        VALUES(?,?,?,?,?,?) ON CONFLICT(kode) DO NOTHING""", KATALOG)


def downgrade():
    # Katalog dapat sudah dipakai oleh pendaftaran, jadwal, dan KRS.
    pass
