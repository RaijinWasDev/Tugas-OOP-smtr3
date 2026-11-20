from alembic import op

revision = "005_pesan"
down_revision = "004_jadwal"


def upgrade():
    op.execute("""CREATE TABLE pesan_jadwal (
        id INTEGER PRIMARY KEY, penerima TEXT NOT NULL, media TEXT NOT NULL,
        pesan TEXT NOT NULL, waktu TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")


def downgrade():
    op.execute("DROP TABLE pesan_jadwal")
