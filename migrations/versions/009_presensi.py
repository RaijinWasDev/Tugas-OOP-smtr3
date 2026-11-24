from alembic import op

revision = "009_presensi"
down_revision = "008_spp"


def upgrade():
    op.execute("""CREATE TABLE sesi_presensi(
        id INTEGER PRIMARY KEY, kode TEXT NOT NULL REFERENCES matakuliah(kode),
        semester INTEGER NOT NULL, tanggal TEXT NOT NULL, mulai INTEGER NOT NULL,
        tutup INTEGER NOT NULL, token_hash TEXT NOT NULL, kedaluwarsa INTEGER NOT NULL,
        UNIQUE(kode,semester,tanggal))""")
    op.execute("""CREATE TABLE peserta_presensi(
        sesi INTEGER NOT NULL REFERENCES sesi_presensi(id), nim TEXT NOT NULL REFERENCES calon_mahasiswa(nim),
        waktu INTEGER, status TEXT CHECK(status IN ('hadir','terlambat')),
        PRIMARY KEY(sesi,nim))""")
    op.execute("CREATE TABLE batas_scan(ip TEXT PRIMARY KEY, awal INTEGER NOT NULL, jumlah INTEGER NOT NULL)")


def downgrade():
    for name in ('batas_scan','peserta_presensi','sesi_presensi'):
        op.execute('DROP TABLE '+name)
