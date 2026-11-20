# KRS · Minggu 5
Proyek memuat API PMB minggu keempat dan API KRS. Dari terminal PowerShell di folder ini:

~~~powershell
python -m pip install -r requirements.txt
python -m alembic upgrade head
$env:PMB_ADMIN_KEY = [guid]::NewGuid().ToString()
$env:PMB_ADMIN_KEY | Set-Clipboard
python -m uvicorn main:app --port 8005
~~~

Buka http://127.0.0.1:8005/docs. Di bagian PMB daftar memakai contoh.json, masukkan kunci demo lewat Authorize, lalu approve ID hasil pendaftaran. Salin NIM dari respons. Di bagian KRS, masukkan NIM tersebut dan semester 1. Setiap pendaftar menggunakan database proyek ini.

| Urutan demo | Hasil |
|---|---|
| POST tambah IF101 (Algoritma) | Draft tercipta dengan 3 SKS |
| Tambah IF101 lagi | Ditolak karena duplikat |
| Tambah IF201 (Struktur Data) | Ditolak karena Algoritma masih semester berjalan |
| Tambah ST101 (Statistika) | Ditolak karena waktunya bertumpuk dengan Algoritma |
| Tambah IF102 (Basis Data) | Diterima, mulai tepat ketika Algoritma selesai. Total 6 SKS |
| GET validasi | Pilihan valid, total 6 SKS |
| DELETE hapus IF102 | Total kembali ke 3 SKS |

## ADR
Saat menambah satu mata kuliah, rantai validator berhenti pada kesalahan pertama agar pemeriksaan berikutnya bisa dilewati. Saat memvalidasi seluruh KRS, mahasiswa menerima daftar pelanggaran. Empat tabel baru adalah matakuliah, prerequisite, krs, dan krs_detail. Nilai disimpan sebagai bobot A=4 sampai E=0; query NOT EXISTS mencari syarat yang belum lulus pada KRS approved di semester terdahulu. Jadwal menggunakan menit sejak tengah malam. Dua jadwal bentrok jika harinya sama dan rentangnya beririsan.

Database latihan menggunakan SQLite seperti PMB. BEGIN IMMEDIATE mengunci penulis sejak sebelum membaca total SKS hingga transaksi selesai. Ini lebih kasar daripada kunci per baris pada MySQL. Hasil uji SQLite tidak membuktikan perilaku MySQL. Keputusan demo: satu jadwal per kode mata kuliah, semester dihitung sebagai nomor urut studi mahasiswa. State machine dan persetujuan dosen dibahas pada minggu keenam.

## Pemeriksaan dan penggunaan AI
Jalankan python -m pytest -q. test_krs.py mencakup percobaan dari dua sesi yang bersamaan, batas tepat 24, dan penolakan di atas batas. explain.txt merekam rencana eksekusi SQLite untuk pemeriksaan prasyarat. Revisi 002 dapat diturunkan ke 001_pmb pada salinan latihan; downgrade menghapus data KRS.

Permintaan aktual Panji: lanjut untuk minggu 5 dengan tautan video PBO. Codex membaca transkrip bahasa Indonesia, menambahkan migrasi, service, API, dan pengujian. Saat demo, catat percobaan dan revisi yang kamu lakukan serta tautan commit. Sumber: https://www.youtube.com/watch?v=FXgKJx-C6zQ
