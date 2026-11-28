"""Data fiktif khusus database latihan."""
from datetime import date, timedelta
import sqlite3

from database import DB_PATH
from tugas.minggu_12_presensi.laporan import sekarang

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


def siapkan():
    if DB_PATH.name != "presentasi.db":
        raise ValueError("Gunakan Buka-Presentasi.cmd untuk menyiapkan data latihan.")
    today = date.today()
    awal = max(date(y,m,1) for y in (today.year-1,today.year) for m in (2,8) if date(y,m,1)<=today)
    with sqlite3.connect(DB_PATH) as db:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("BEGIN IMMEDIATE")
        db.execute("CREATE TABLE IF NOT EXISTS paket_presentasi (versi INTEGER PRIMARY KEY)")
        if db.execute("SELECT 1 FROM paket_presentasi WHERE versi=1").fetchone():
            return
        db.execute("INSERT INTO program_studi VALUES (2,'002','Sistem Informasi','Fakultas Teknik')")
        db.executemany("INSERT INTO matakuliah VALUES(?,?,?,?,?,?)", KATALOG)
        for i,(nama,prodi) in enumerate([("Rina Larasati",2),("Budi Pratama",1),("Nadia Putri",2)],1):
            nim=None if i==1 else f"{today.year}{prodi:03d}-{i:04d}"
            db.execute("""INSERT INTO calon_mahasiswa(nama_lengkap,email,phone,tanggal_lahir,alamat,
                program_studi_id,jalur_masuk_id,status,nim) VALUES(?,?,?,'2006-03-10','Jakarta',?,1,?,?)""",
                (nama,f"latihan{i}@example.invalid",f"08123456780{i}",prodi,"approved" if nim else "pending",nim))
            if nim:
                bill=db.execute("INSERT INTO billing(nim,awal,tempo,pokok) VALUES(?,?,?,5000000)",
                                (nim,awal,awal+timedelta(days=14))).lastrowid
                db.execute("INSERT INTO payment VALUES(?,?,5000000,'manual',?)",(f"LAT-{i}",bill,awal))
                krs=db.execute("INSERT INTO krs(nim,semester,status) VALUES(?,1,?)",
                               (nim,"approved" if i==2 else "draft")).lastrowid
                kode="TI103" if i==2 else "SI101"
                db.execute("INSERT INTO krs_detail(krs_id,kode_mk) VALUES(?,?)",(krs,kode))
                db.execute("INSERT INTO jadwal VALUES(?,'A101',?)",(kode,"Ratna Sari" if i==2 else "Dimas Putra"))
                if i==2:
                    hari=sekarang().date()-timedelta(days=7)
                    hari-=timedelta(days=(hari.weekday()-2)%7)
                    mulai=sekarang().replace(year=hari.year,month=hari.month,day=hari.day,hour=8,minute=0,second=0,microsecond=0)
                    t=int(mulai.timestamp())
                    sesi=db.execute("INSERT INTO sesi_presensi(kode,semester,tanggal,mulai,tutup,token_hash,kedaluwarsa) VALUES(?,1,?,?,?,?,?)",
                                    (kode,hari,t,t+1800,"latihan-selesai",t+900)).lastrowid
                    db.execute("INSERT INTO peserta_presensi VALUES(?,?,?,'hadir')",(sesi,nim,t+60))
        db.execute("INSERT INTO paket_presentasi VALUES(1)")


if __name__=="__main__":
    siapkan()
