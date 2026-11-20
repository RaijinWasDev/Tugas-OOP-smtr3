from alembic import op

revision = "002_krs"
down_revision = "001_pmb"

def upgrade():
    op.execute("""CREATE TABLE matakuliah(
      kode TEXT PRIMARY KEY, nama TEXT NOT NULL, sks INTEGER NOT NULL CHECK(sks BETWEEN 1 AND 4),
      hari INTEGER NOT NULL CHECK(hari BETWEEN 1 AND 7),
      mulai INTEGER NOT NULL CHECK(mulai>=0), selesai INTEGER NOT NULL CHECK(selesai<=1440 AND selesai>mulai))""")
    op.execute("""CREATE TABLE krs(id INTEGER PRIMARY KEY, nim TEXT NOT NULL REFERENCES calon_mahasiswa(nim),
      semester INTEGER NOT NULL CHECK(semester>0), status TEXT NOT NULL DEFAULT 'draft'
      CHECK(status IN ('draft','revision','submitted','approved')), UNIQUE(nim,semester))""")
    op.execute("""CREATE TABLE krs_detail(krs_id INTEGER NOT NULL REFERENCES krs(id) ON DELETE CASCADE,
      kode_mk TEXT NOT NULL REFERENCES matakuliah(kode), bobot INTEGER CHECK(bobot BETWEEN 0 AND 4),
      PRIMARY KEY(krs_id,kode_mk))""")
    op.execute("""CREATE TABLE prerequisite(kode_mk TEXT NOT NULL REFERENCES matakuliah(kode),
      syarat TEXT NOT NULL REFERENCES matakuliah(kode), PRIMARY KEY(kode_mk,syarat), CHECK(kode_mk<>syarat))""")
    op.execute("""INSERT INTO matakuliah VALUES ('IF101','Algoritma',3,1,480,600),
      ('IF201','Struktur Data',3,2,480,600),('ST101','Statistika',3,1,540,660),
      ('IF102','Basis Data',3,1,600,720)""")
    op.execute("INSERT INTO prerequisite VALUES ('IF201','IF101')")

def downgrade():
    for table in ("prerequisite","krs_detail","krs","matakuliah"):
        op.execute("DROP TABLE "+table)
