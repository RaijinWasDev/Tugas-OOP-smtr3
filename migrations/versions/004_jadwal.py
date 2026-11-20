from alembic import op

revision = "004_jadwal"
down_revision = "003_workflow"


def upgrade():
    op.execute("CREATE TABLE ruangan (kode TEXT PRIMARY KEY, kapasitas INTEGER NOT NULL CHECK(kapasitas > 0))")
    op.execute("INSERT INTO ruangan VALUES ('A101', 40), ('B202', 25)")
    op.execute("""CREATE TABLE jadwal (
        kode TEXT PRIMARY KEY REFERENCES matakuliah(kode),
        ruangan TEXT NOT NULL REFERENCES ruangan(kode), dosen TEXT NOT NULL COLLATE NOCASE
    )""")


def downgrade():
    op.execute("DROP TABLE jadwal")
    op.execute("DROP TABLE ruangan")
