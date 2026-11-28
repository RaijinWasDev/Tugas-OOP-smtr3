"""Kurikulum contoh TI/SI. Susunan lokal mengacu pada materi program sarjana Fasilkom UI."""
from alembic import op

revision = "011_kurikulum"
down_revision = "010_katalog"

PROGRAM = {
    "TI": [
        "Dasar Pemrograman|Matematika Diskret|Kalkulus I|Pengantar Sistem Digital|Bahasa Inggris Akademik|Pancasila dan Kewarganegaraan",
        "Struktur Data dan Algoritma|Pemrograman Berorientasi Objek|Aljabar Linear|Organisasi Komputer|Statistika dan Probabilitas|Agama dan Etika",
        "Sistem Operasi|Basis Data|Perancangan dan Analisis Algoritma|Jaringan Komputer|Interaksi Manusia dan Komputer|Komunikasi Ilmiah",
        "Rekayasa Perangkat Lunak|Pemrograman Web|Kecerdasan Artifisial|Teori Bahasa dan Automata|Metode Numerik|Etika Profesi Informatika",
        "Pembelajaran Mesin|Sistem Terdistribusi|Keamanan Informasi|Grafika Komputer|Pemrograman Perangkat Bergerak|Manajemen Proyek Perangkat Lunak",
        "Rekayasa Data|Komputasi Awan|Proyek Pengembangan Perangkat Lunak|Pengujian Perangkat Lunak|Pengolahan Citra|Metodologi Penelitian",
        "Kerja Praktik|Pemrosesan Bahasa Alami|Arsitektur Perangkat Lunak|Seminar Proposal",
        "Tugas Akhir|Seminar Hasil dan Publikasi"],
    "SI": [
        "Dasar Pemrograman Bisnis|Pengantar Sistem Informasi|Matematika Diskret|Pengantar Manajemen|Bahasa Inggris Akademik|Pancasila dan Kewarganegaraan",
        "Struktur Data|Sistem Informasi Manajemen|Statistika Bisnis|Arsitektur Komputer|Prinsip Akuntansi|Agama dan Etika",
        "Basis Data|Analisis dan Perancangan Sistem|Pemodelan Proses Bisnis|Sistem Operasi|Komunikasi Bisnis|Perilaku Organisasi",
        "Pengembangan Aplikasi Web|Sistem Enterprise|Manajemen Data|Jaringan dan Infrastruktur TI|Interaksi Manusia dan Komputer|Etika Profesi SI",
        "Manajemen Proyek Sistem Informasi|Analitika Bisnis|Integrasi Aplikasi Enterprise|Sistem Pendukung Keputusan|Manajemen Layanan TI|Perancangan Pengalaman Pengguna",
        "Proyek Pengembangan Sistem Informasi|Arsitektur Enterprise|Gudang Data dan Inteligensi Bisnis|Audit Sistem Informasi|Manajemen Risiko TI|Metodologi Penelitian",
        "Kerja Praktik|Tata Kelola TI|Strategi Transformasi Digital|Seminar Proposal",
        "Tugas Akhir|Seminar Hasil dan Publikasi"]}
BEBAN = [(4,4,3,3,3,3)]*2 + [(4,4,4,3,3,3)]*4 + [(4,4,3,3),(4,2)]
DOSEN = ["Laras Widyasena","Arka Mahendra","Nadia Kartikasari","Bayu Pranata","Sekar Andini","Raka Wijaya",
         "Galih Wicaksana","Kirana Prameswari","Dimas Wiratama","Nara Kusumadewi","Tara Adinata","Ayu Rengganis"]


def upgrade():
    c=op.get_bind()
    op.execute("""CREATE TABLE kurikulum(kode TEXT PRIMARY KEY REFERENCES matakuliah(kode),
        prodi_id INTEGER NOT NULL REFERENCES program_studi(id),semester INTEGER NOT NULL)""")
    for idx,(prefix,terms) in enumerate(PROGRAM.items()):
        nama=("Teknik Informatika","Sistem Informasi")[idx]
        prodi=c.exec_driver_sql("SELECT id FROM program_studi WHERE nama=?",(nama,)).scalar_one()
        for sem,(names,weights) in enumerate(zip(terms,BEBAN,strict=True),1):
            room=f"{prefix}-{sem}01"
            c.exec_driver_sql("INSERT INTO ruangan VALUES(?,40)",(room,))
            for j,(name,sks) in enumerate(zip(names.split("|"),weights,strict=True)):
                code=f"{prefix}-{sem}{j+1:02}"
                slot=(j+sem-1)%15
                hari=slot%5+1
                mulai=450+210*(slot//5)
                dosen=DOSEN[idx*6+j]
                c.exec_driver_sql("INSERT INTO matakuliah VALUES(?,?,?,?,?,?)",(code,name,sks,hari,mulai,mulai+50*sks))
                c.exec_driver_sql("INSERT INTO jadwal VALUES(?,?,?)",(code,room,dosen))
                c.exec_driver_sql("INSERT INTO kurikulum VALUES(?,?,?)",(code,prodi,sem))
    op.execute("""CREATE TRIGGER kurikulum_isi BEFORE INSERT ON krs_detail
      WHEN EXISTS(SELECT 1 FROM kurikulum WHERE kode=NEW.kode_mk) BEGIN
      SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM krs k JOIN calon_mahasiswa m USING(nim)
      JOIN kurikulum u ON u.prodi_id=m.program_studi_id WHERE k.id=NEW.krs_id AND u.kode=NEW.kode_mk)
      THEN RAISE(ABORT,'Mata kuliah di luar prodi') END;
      SELECT CASE WHEN (SELECT semester FROM krs WHERE id=NEW.krs_id)<=2 AND
      (SELECT COALESCE(SUM(m.sks),0) FROM krs_detail d JOIN matakuliah m ON m.kode=d.kode_mk WHERE d.krs_id=NEW.krs_id)
      +(SELECT sks FROM matakuliah WHERE kode=NEW.kode_mk)>20 THEN RAISE(ABORT,'Batas semester awal 20 SKS') END; END""")
    op.execute("""CREATE TRIGGER kurikulum_submit BEFORE UPDATE OF status ON krs WHEN NEW.status='submitted'
      AND NEW.semester<=2 AND EXISTS(SELECT 1 FROM krs_detail d JOIN kurikulum u ON u.kode=d.kode_mk WHERE d.krs_id=NEW.id)
      AND (SELECT SUM(m.sks) FROM krs_detail d JOIN matakuliah m ON m.kode=d.kode_mk WHERE d.krs_id=NEW.id)<>20
      BEGIN SELECT RAISE(ABORT,'Semester 1 dan 2 wajib 20 SKS'); END""")


def downgrade():
    op.execute("DROP TRIGGER kurikulum_submit")
    op.execute("DROP TRIGGER kurikulum_isi")
    op.execute("DROP TABLE kurikulum")
