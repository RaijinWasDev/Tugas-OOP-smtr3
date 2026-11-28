# Sevima Mini

## Menjalankan portal admin di Windows

Gunakan Python 3.11. Untuk versi lengkap, ambil branch `tugas/minggu-12`. Pada instalasi pertama, jalankan di PowerShell:

~~~powershell
git clone --branch tugas/minggu-12 https://github.com/RaijinWasDev/Tugas-OOP-smtr3.git
cd Tugas-OOP-smtr3
python -m pip install -r requirements.txt
.\Buka-Sevima.cmd
~~~

Jika sudah mengunduh dan mengekstrak ZIP dari GitHub, buka terminal di folder yang berisi `main.py`, lalu jalankan dua perintah terakhir. Untuk pemakaian berikutnya cukup buka `Buka-Sevima.cmd` di folder tersebut.

Setelah terminal menampilkan **Uvicorn running**, buka http://127.0.0.1:8007/admin di laptop yang menjalankan program. Gunakan kunci admin dari terminal itu. Launcher menyiapkan database lokal saat pertama dijalankan. Di Ringkasan, jelajahi katalog TI dan SI atau buka laporan UML. Untuk praktik, setujui pendaftar di Pendaftaran, lalu pilih mahasiswa dan mata kuliah di KRS.

Tekan Ctrl+C di terminal untuk menghentikan server. Jika port 8007 sedang dipakai, hentikan server lama atau jalankan `.\Buka-Sevima.cmd 8008` dan buka alamat yang tercetak. Kedua port menjalankan aplikasi dan database dari folder proyek yang sama.

## Tugas mingguan

- [Minggu 1 � rancangan](tugas/minggu_01_rancangan/)
- [Minggu 2 � uml](tugas/minggu_02_uml/)
- [Minggu 3 � pendaftaran pmb](tugas/minggu_03_pendaftaran_pmb/)
- [Minggu 4 � persetujuan pmb](tugas/minggu_04_persetujuan_pmb/)
- [Minggu 5 � pengisian krs](tugas/minggu_05_pengisian_krs/)
- [Minggu 6 � persetujuan krs](tugas/minggu_06_persetujuan_krs/)
- [Minggu 7 � jadwal ruangan](tugas/minggu_07_jadwal_ruangan/)

[Pengumpulan UTS](UTS/README.md) � [Contoh pendaftar](contoh/pendaftar.json)

[Minggu 8 - Perubahan jadwal dan notifikasi](tugas/minggu_08_perubahan_jadwal/)

- [Minggu 9 — input nilai, IPS/IPK dan riwayat](tugas/minggu_09_nilai/)

- [Minggu 11 — Keuangan SPP](tugas/minggu_11_keuangan/)

- [Minggu 12 — Presensi QR](tugas/minggu_12_presensi/)



## Kurikulum TI dan SI

Setiap prodi memiliki 42 mata kuliah (144 SKS). Rekomendasi per semester: 20, 20, 21, 21, 21, 21, 14, 6 SKS. Semester 1 dan 2 memerlukan 20 SKS untuk diajukan. Mulai semester 3 batas pengisian adalah 24 SKS. Progres lulus menjumlahkan mata kuliah berbeda dalam kurikulum yang memiliki nilai lulus pada KRS disetujui. Nama dosen, ruangan, jadwal, kode, bobot dan pembagian semester disusun untuk aplikasi. Topik mengacu pada program Sarjana Ilmu Komputer dan Sistem Informasi Fasilkom UI:
https://cs.ui.ac.id/sarjana-ilmu-komputer/
https://cs.ui.ac.id/sarjana-sistem-informasi/
