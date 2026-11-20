from alembic import op

revision = "007_nilai"
down_revision = "006_outbox"


def upgrade():
    op.execute("""CREATE TABLE skala_nilai (
        huruf TEXT PRIMARY KEY, bobot NUMERIC(3,2) NOT NULL UNIQUE CHECK(bobot BETWEEN 0 AND 4),
        lulus BOOLEAN NOT NULL CHECK(lulus IN (0,1)))""")
    op.execute("INSERT INTO skala_nilai VALUES ('A',4,1),('B',3,1),('C',2,1),('D',1,0),('E',0,0)")
    op.execute("ALTER TABLE krs_detail ADD COLUMN nilai TEXT REFERENCES skala_nilai(huruf)")
    op.execute("UPDATE krs_detail SET nilai=(SELECT huruf FROM skala_nilai WHERE skala_nilai.bobot=krs_detail.bobot)")
    op.execute("""CREATE TABLE grade_history (
        id INTEGER PRIMARY KEY, krs_id INTEGER NOT NULL, kode_mk TEXT NOT NULL,
        lama TEXT, baru TEXT NOT NULL, dosen TEXT NOT NULL, alasan TEXT,
        waktu TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(krs_id,kode_mk) REFERENCES krs_detail(krs_id,kode_mk))""")


def downgrade():
    op.execute("DROP TABLE grade_history")
    op.execute("ALTER TABLE krs_detail DROP COLUMN nilai")
    op.execute("DROP TABLE skala_nilai")
