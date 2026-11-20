Panduan versi sekarang: [jalankan portal dari folder utama](../../README.md). Catatan di bawah mendokumentasikan versi mingguan pada tag `minggu-06`.

# Sevima Mini · Minggu 6
## Menjalankan demo
Buka PowerShell di folder minggu-06.
~~~powershell
python -m pip install -r requirements.txt
python -m alembic upgrade head
$env:PMB_ADMIN_KEY = [guid]::NewGuid().ToString()
$env:PMB_ADMIN_KEY | Set-Clipboard
python -m uvicorn main:app --port 8006
~~~
Buka http://127.0.0.1:8006/docs. Daftarkan data contoh.json, lalu Authorize dengan kunci admin dari clipboard dan setujui pendaftaran PMB. Salin NIM dari respons. Seluruh aksi berikut menggunakan semester 1.
1. Tambah IF101. Simpan version dari respons.
2. Jalankan submit dengan header X-Nim berisi NIM tadi dan body {"version":2} jika versi terakhir memang 2. Status berubah menjadi submitted.
3. Jalankan revise dengan X-Dosen-Pa berisi PA01, versi terbaru dan catatan "Tambahkan Basis Data". Perhatikan status revision.
4. Tambah IF102, baca version baru, lalu submit lagi.
5. Jalankan approve dengan PA01 dan version terbaru. KRS menjadi approved dan pilihan mata kuliah terkunci.
6. Untuk memperlihatkan konflik, kirim versi sebelumnya atau coba hapus IF101 setelah disetujui.

## Keputusan desain
Tabel empat transisi cukup kecil untuk diperiksa satu per satu. Submit mengulang validasi seluruh KRS dan menolak KRS kosong. Hanya pemilik atau PA yang ditugaskan dapat menjalankan aksi terkait. Pada demo lokal, PA01 adalah pembimbing awal dan identitas aktor berasal dari header simulasi, sehingga belum memberikan autentikasi pengguna. Setiap edit menaikkan versi. Semua perubahan memakai transaksi SQLite dengan BEGIN IMMEDIATE. Status, waktu, audit dan notifikasi masuk dalam satu commit. Notifikasi berupa catatan tersimpan.

## Pengujian
Jalankan python -m pytest -q setelah dependensi terpasang. test_workflow.py memeriksa 32 kombinasi status dan peran, alur pengajuan dengan revisi, konflik versi, rollback jika notifikasi gagal, dan 1.000 percobaan acak dengan seed tetap. test_hypothesis.py menambahkan property test dengan max_examples=1000 menggunakan validator proyek dan pemeriksaan slot jadwal independen.

## Log AI dan OPAR
Panji meminta implementasi dari video PBO minggu 06 dan modul KRS minggu 5–6. ChatGPT/Codex membuat migrasi, workflow, endpoint dan tes dari basis minggu kelima. Catatan teknis berbantuan AI untuk ditinjau saat rekaman:
- Observe: dua pihak bisa membaca versi pengajuan yang sama.
- Plan: periksa identitas, status dan versi di dalam transaksi terkunci.
- Act: implementasikan transisi, audit dan notifikasi; paksa penyimpanan notifikasi gagal pada database tes.
- Reflect: rollback menjaga konsistensi dan nomor versi mendeteksi data lama. Login terverifikasi masih dibutuhkan bila dipakai di luar simulasi lokal.

Tambahkan refleksi pribadi dan tautan commit setelah melakukan demo. Sumber video https://youtu.be/C66tdSW8kU4
