from alembic import op

revision = "006_outbox"
down_revision = "005_pesan"


def upgrade():
    op.execute("""CREATE TABLE outbox_jadwal (
        id INTEGER PRIMARY KEY, kode TEXT NOT NULL, payload TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending', gagal TEXT, percobaan INTEGER NOT NULL DEFAULT 0)""")
    op.execute("CREATE INDEX ix_outbox_pending ON outbox_jadwal(status,id)")
    op.execute("CREATE INDEX ix_outbox_kode ON outbox_jadwal(kode,id)")
    op.execute("ALTER TABLE pesan_jadwal ADD COLUMN event_id INTEGER REFERENCES outbox_jadwal(id)")
    op.execute("CREATE UNIQUE INDEX uq_jadwal_delivery ON pesan_jadwal(event_id,media,penerima)")


def downgrade():
    op.execute("DROP INDEX uq_jadwal_delivery")
    op.execute("ALTER TABLE pesan_jadwal DROP COLUMN event_id")
    op.execute("DROP TABLE outbox_jadwal")
