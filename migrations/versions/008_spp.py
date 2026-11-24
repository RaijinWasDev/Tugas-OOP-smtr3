from alembic import op

revision = "008_spp"
down_revision = "007_nilai"


def upgrade():
    op.execute("CREATE TABLE payment_method (kode TEXT PRIMARY KEY)")
    op.execute("INSERT INTO payment_method VALUES ('manual'),('gateway')")
    op.execute("""CREATE TABLE billing (id INTEGER PRIMARY KEY, nim TEXT NOT NULL REFERENCES calon_mahasiswa(nim),
        awal DATE NOT NULL, tempo DATE NOT NULL, pokok INTEGER NOT NULL CHECK(pokok>0),
        UNIQUE(nim,awal))""")
    op.execute("""CREATE TABLE payment (id TEXT PRIMARY KEY, billing_id INTEGER NOT NULL REFERENCES billing(id),
        jumlah INTEGER NOT NULL CHECK(jumlah>0), metode TEXT NOT NULL REFERENCES payment_method(kode),
        tanggal DATE NOT NULL DEFAULT (date('now','localtime')))""")
    op.execute("CREATE INDEX ix_payment_bill ON payment(billing_id)")
    op.execute("""CREATE TABLE email_spp (id TEXT PRIMARY KEY, penerima TEXT NOT NULL, pesan TEXT NOT NULL,
        terkirim TEXT)""")
    op.execute("""CREATE VIEW saldo_spp AS WITH saldo AS (
        SELECT b.*,COALESCE(SUM(p.jumlah),0) dibayar FROM billing b LEFT JOIN payment p ON p.billing_id=b.id
        GROUP BY b.id), biaya AS (SELECT saldo.*, CASE WHEN tempo<date('now','localtime') AND
        COALESCE((SELECT SUM(jumlah) FROM payment WHERE billing_id=saldo.id AND tanggal<=saldo.tempo),0)<pokok
        THEN (pokok+99)/100 ELSE 0 END denda FROM saldo)
        SELECT biaya.*,MAX(0,pokok+denda-dibayar) sisa, CASE WHEN dibayar>=pokok+denda THEN 'paid'
        WHEN tempo<date('now','localtime') THEN 'overdue' WHEN dibayar>0 THEN 'partial'
        ELSE 'unpaid' END status FROM biaya""")
    for name, table, event, nim in [
        ("isi","krs_detail","INSERT","(SELECT nim FROM krs WHERE id=NEW.krs_id)"),
        ("ajukan","krs","UPDATE OF status","NEW.nim")]:
        kondisi = "NEW.status='submitted' AND " if name=="ajukan" else ""
        op.execute(f"""CREATE TRIGGER spp_{name} BEFORE {event} ON {table} WHEN {kondisi}
            EXISTS(SELECT 1 FROM saldo_spp WHERE nim={nim} AND status='overdue')
            BEGIN SELECT RAISE(ABORT,'SPP tertunggak'); END""")


def downgrade():
    for name in ("isi","ajukan"):
        op.execute("DROP TRIGGER spp_"+name)
    op.execute("DROP VIEW saldo_spp")
    for name in ("email_spp","payment","billing","payment_method"):
        op.execute("DROP TABLE "+name)

