from alembic import op

revision = "003_workflow"
down_revision = "002_krs"

def upgrade():
    for definition in ("version INTEGER NOT NULL DEFAULT 1", "dosen_pa_id TEXT NOT NULL DEFAULT 'PA01'",
                       "submitted_at TEXT", "approved_at TEXT", "catatan TEXT"):
        op.execute("ALTER TABLE krs ADD COLUMN " + definition)
    op.execute("""CREATE TABLE krs_log(id INTEGER PRIMARY KEY, krs_id INTEGER NOT NULL REFERENCES krs(id),
               asal TEXT NOT NULL, tujuan TEXT NOT NULL, aktor TEXT NOT NULL, catatan TEXT,
               waktu TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
    op.execute("""CREATE TABLE notifikasi(id INTEGER PRIMARY KEY, krs_id INTEGER NOT NULL REFERENCES krs(id),
               penerima TEXT NOT NULL, pesan TEXT NOT NULL, waktu TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")

def downgrade():
    op.execute("DROP TABLE notifikasi")
    op.execute("DROP TABLE krs_log")
    for col in ("catatan","approved_at","submitted_at","dosen_pa_id","version"):
        op.execute("ALTER TABLE krs DROP COLUMN "+col)
